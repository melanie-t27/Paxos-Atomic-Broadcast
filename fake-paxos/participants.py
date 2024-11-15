'''
from abc import abstractmethod
import sys
import socket
import struct
from .messages import Message
from messages import *
import pickle
import math
from collections import defaultdict

def mcast_receiver(hostport  : tuple[str, int]):
    """create a multicast socket listening to the address"""
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    recv_sock.bind(hostport)

    mcast_group = struct.pack("4sl", socket.inet_aton(hostport[0]), socket.INADDR_ANY)
    recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_group)
    return recv_sock


def mcast_sender():
    """create a udp socket"""
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    return send_sock


# Abstract Base Class for Paxos Participants
class Participant:
    def __init__(self, id : int, config : dict[str, tuple[str, int]]):
        # Unique identifier for participant
        self.id = id
        # Configuration
        self.config = config
        # Id instance
        self.id_instance = -1

    @abstractmethod
    def receive_message(self, message : bytes):
        """Method to receive messages from other participants (e.g., proposals, prepare messages)."""
        pass

    @abstractmethod
    def send_message(self, message : Message):
        """Method to send messages to other participants."""
        pass

    @abstractmethod
    def run(self):
        """Method to run the logic of the participant for a given round."""
        pass


# Acceptor Class: A participant that accepts or rejects proposals
class Acceptor(Participant):
    def __init__(self, id : int, config : dict[str, tuple[str, int]]):
        super().__init__(id, config)
        # The highest-numbered round in which the acceptor has casted a vote, one for each instance
        self.v_rnd : list[int] = list()
        # The value this Acceptor has accepted (if any), one for each instance
        self.v_val : list[int] = list()
        # Round number to track which round this Acceptor is in, one for each instance
        self.round : list[int] = list()
        # Sockets
        self.r = mcast_receiver(config["acceptors"])
        self.s = mcast_sender()

    def receive_message(self, message : bytes):
        msg : Message = pickle.loads(message)
        if isinstance(msg, Message1A):
            # If the message is a prepare request, handle the prepare phase
            self.handle_prepare(msg)
        elif isinstance(msg, Message2A):
            # If the message is a proposal, handle the proposal phase
            self.handle_propose(msg)

    def send_message(self, message : Message):
        self.s.sendto(pickle.dumps(Message), self.config["proposers"])

    def handle_prepare(self, message : Message1A):
        if message.c_rnd > self.round[message.id_instance]:
            self.round[message.id_instance] = message.c_rnd
            msg : Message = Message1B(self.id, message.id_instance, self.round[message.id_instance],
                                       self.v_rnd[message.id_instance], self.v_val)
            self.send_message(msg)

    def handle_propose(self, message : Message2A):
        if message.c_rnd >= self.round[message.id_instance]:
            self.v_rnd[message.id_instance] = message.c_rnd
            self.v_val = message.c_val
            msg : Message = Message2B(self.id, message.id_instance, self.v_rnd[message.id_instance], self.v_val)
            self.send_message(msg)

    def run(self):
        print("Process {}-{} started.".format(self.__class__.__name__, self.id))
        sys.stdout.flush()
        while True:
            # Acceptor listens for incoming messages
            message = self.r.recv(1024)
            self.receive_message(message)

        
# Proposer Class: A participant that proposes a value to be accepted by the acceptors
class Proposer(Participant):
    def __init__(self, id : int, config : dict[str, tuple[str, int]],
                 num_acceptors : int, num_proposers : int):
        super().__init__(id, config)
        # Obtained value from client
        self.v : list[int] = list()
        # Proposal round number (unique and increasing within proposers of the same paxos instance)
        self.c_rnd : int = id
        # Proposal value for this proposer picked at round proposal_round
        self.c_val : list[int] = list()
        # Size of the quorum
        self.quorum_size : int = math.ceil(num_acceptors / 2) 
        # Number of proposers
        self.num_proposers : int = num_proposers
        # Dictionary to track responses per round
        self.round_responses: set[tuple[int,list[int]]] = set()
        # Sockets
        self.r = mcast_receiver(config["proposers"])
        self.s = mcast_sender()

    def send_message(self, message : Message):
        if isinstance(message, Message1A) or isinstance(message, Message2A):
            self.s.sendto(pickle.dumps(message), self.config["acceptors"])
        elif isinstance(message, DecisionMessage):
            self.s.sendto(pickle.dumps(message), self.config["learners"])

    def receive_message(self, message : bytes):
        msg: Message = pickle.loads(message)
        if isinstance(msg, Message1B):
            self.handle_promise(msg)
        elif isinstance(msg, Message2B):
            self.handle_acceptance(msg)
        elif isinstance(msg, ClientMessage):
            self.handle_client(msg)

    def handle_promise(self, message : Message1B):
        if message.rnd == self.c_rnd:
            self.round_responses.add((message.v_rnd, message.v_val)) 
            if len(self.round_responses) >= self.quorum_size:
                k = max(t[0] for t in self.round_responses) 
                v = {t for t in self.round_responses if t[0] == k}
                if k == 0:
                    self.c_val = self.v
                else:
                    self.c_val = list(v)[0][1] # Get the second element of the tuple, they are all equal
                self.round_responses = set()
                msg: Message = Message2A(self.id, message.id_instance, self.c_rnd, self.c_val)
                self.send_message(msg)
                
        
    def handle_acceptance(self, message : Message2B):
        if message.v_rnd == self.c_rnd:
            self.round_responses.add((message.v_rnd, message.v_val)) 
            if len(self.round_responses) >= self.quorum_size:
                msg: Message = DecisionMessage(self.id, message.id_instance, list(self.round_responses)[0][1])
                self.round_responses = set()
                self.send_message(msg)


    def handle_client(self, message : ClientMessage):
        #self.v.append(message.values)  # Set the proposed value from the client
        self.propose()

    def propose(self):
        # Increment the proposal number (acts as the round number) for each new proposal
        self.c_rnd = self.c_rnd + self.num_proposers
        # Send prepare messages to all acceptors
        msg : Message = Message1A(self.id, self.id_instance, self.c_rnd)
        self.send_message(msg)

    def run(self):
        print("Process {}-{} started.".format(self.__class__.__name__, self.id))
        sys.stdout.flush()
        while True:
            message = self.r.recv(1024)
            self.receive_message(message)


# Learner Class: A participant that learns the value once it has been accepted
class Learner(Participant):
    def __init__(self, id : int, config : dict[str, tuple[str, int]]):
        super().__init__(id, config)
        # The value learned by the Learner once it's accepted
        self.learned_values : list[int] = list()
        # Sockets
        self.r = mcast_receiver(config["learners"])

    def send_message(self, message: Message):
        # Learners don't send any message
        pass

    def receive_message(self, message: bytes):
        msg: Message = pickle.loads(message)
        if isinstance(msg, DecisionMessage):
            self.learned_values = msg.v_val

    def run(self):
        print("Process {}-{} started.".format(self.__class__.__name__, self.id))
        sys.stdout.flush()
        while True:
            message = self.r.recv(1024)
            self.receive_message(message)



class Client(Participant):
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        super().__init__(id, config)
        # Vector of all values 
        self.values : list[int] = list()
        # Socket
        self.s = mcast_sender()

    def receive_message(self, message: bytes):
        pass

    def send_message(self, message: Message):
        self.s.sendto(pickle.dumps(message), self.config["proposers"])

    def submit_value(self, values: list[int]):
        message: Message = ClientMessage(self.id, 0, values)
        self.send_message(message)

    def run(self):
        print(f"Process {self.__class__.__name__}-{self.id} started. Enter values to propose:")
        while True:
            try:
                value = int(input())
                self.values.append(value)
            except ValueError:
                print("Please enter an integer.")
        self.submit_value(self.values)
'''
from .messages import Message
from utils import *
from collections import defaultdict
import threading
import pickle

class Acceptor:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        self.id_instance = 0
        # The highest-numbered round in which the acceptor has casted a vote, one for each instance
        self.v_rnd : defaultdict[int,int] = defaultdict(int)
        # The value this Acceptor has accepted (if any), one for each instance
        self.v_val : defaultdict[int,list[int]] = defaultdict(list)
        # Round number to track which round this Acceptor is in, one for each instance
        self.round : defaultdict[int,int] = defaultdict(int)
        # Lock
        self.lock = threading.RLock()
        # Acceptor state
        self.state : State = Phase1BState(self)
        # Sockets
        self.r = mcast_receiver(config["acceptors"])
        self.s = mcast_sender()
    
    def send_message(self, message : Message):
        self.s.sendto(pickle.dumps(Message), self.config["proposers"])

    def handle_prepare(self, message : Message1A):
        if message.c_rnd > self.round[message.id_instance]:
            self.round[message.id_instance] = message.c_rnd
            self.send_message(
                Message1B(self.id, message.id_instance, self.round[message.id_instance],
                                       self.v_rnd[message.id_instance], self.v_val[message.id_instance]))
    
    def handle_propose(self, message : Message2A):
        if message.c_rnd >= self.round[message.id_instance]:
            self.v_rnd[message.id_instance] = message.c_rnd
            self.v_val[message.id_instance] = message.c_val
            self.send_message(Message2B(self.id, message.id_instance, self.v_rnd[message.id_instance], 
                                        self.v_val[message.id_instance]))

    def set_state(self, state : State):
        self.state = state

    def run(self):
        while True:
            msg : bytes = self.r.recv(1024)
            self.state.on_event(pickle.loads(msg))

########################## STATES FOR STATE MACHINE ##########################

class Phase1BState(State):
    def __init__(self, acceptor: Acceptor):
        self.acceptor = acceptor
        # Set timer for 1A message arrival
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()

    def on_event(self, event : Message):
        with self.acceptor.lock:
            if isinstance(event, Message1A):
                # Send messages 1B to proposers
                self.acceptor.handle_prepare(event)
                # Change state
                self.acceptor.set_state(Phase2BState(self.acceptor))

    def on_timeout(self):
        # Restar timer
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()
    

class Phase2BState(State):
    def __init__(self, acceptor: Acceptor):
        self.acceptor = acceptor
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()

    def on_event(self, event: Message):
        with self.acceptor.lock:
            if isinstance(event, Message2A):
                # Send message 2B to proposers 
                self.acceptor.handle_propose(event)
                # Change state
                self.acceptor.set_state(Phase1BState(self.acceptor))

    def on_timeout(self):
        # Change state
        self.acceptor.set_state(Phase1BState(self.acceptor))

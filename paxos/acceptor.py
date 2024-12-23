from messages import Message
from utils import *
from collections import defaultdict
import threading
import pickle

########################## ACCEPTOR ##########################
class Acceptor:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # The highest-numbered round in which the acceptor has casted a vote, one for each instance
        self.v_rnd : defaultdict[int,int] = defaultdict(int)
        # The value this Acceptor has accepted (if any), one for each instance
        self.v_val : defaultdict[int,list[tuple[int,int]]] = defaultdict(list)
        # Round number to track which round this Acceptor is in, one for each instance
        self.round : defaultdict[int,int] = defaultdict(int)
        # Lock
        self.lock = threading.RLock()
        # Sockets
        self.r = mcast_receiver(config["acceptors"])
        self.s = mcast_sender()
    
    def send_message(self, message : Message):
        with self.lock:
            self.s.sendto(pickle.dumps(message), self.config["proposers"])

    def handle_prepare(self, message : Message1A):
        # Phase 1B
        with self.lock:
            if message.c_rnd > self.round[message.id_instance]:
                self.round[message.id_instance] = message.c_rnd
                val, id = to_list_and_id(self.v_val[message.id_instance])
                msg : Message1B = Message1B(message.id_instance, self.round[message.id_instance],
                                        self.v_rnd[message.id_instance], val, id)
                self.send_message(msg)
            
    
    def handle_propose(self, message : Message2A):
        # Phase 2B
        with self.lock:
            if message.c_rnd >= self.round[message.id_instance]:
                self.v_rnd[message.id_instance] = message.c_rnd
                self.v_val[message.id_instance] = from_list_and_id((message.c_val, message.id_source))
                val, id = to_list_and_id(self.v_val[message.id_instance])
                msg : Message2B = Message2B(message.id_instance, self.v_rnd[message.id_instance], val, id)
                self.send_message(msg)

    def run(self):
        while True:
            msg : bytes = self.r.recv(2**16)
            event : Message = pickle.loads(msg)
            with self.lock:
                if isinstance(event, Message1A):
                    # Send messages 1B to proposers
                    self.handle_prepare(event)
                elif isinstance(event, Message2A):
                    # Send message 2B to proposers 
                    self.handle_propose(event)
                    
from utils import *
from communication import *
import pickle

class Learner:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # Sockets
        self.r = mcast_receiver(config["learners"])
        # Decided value (each message is represented by its value and the client id that sent it) and related instance
        self.d_val : list[int] = list()
        self.id_instance = -1

    def receive_decision(self, decision : DecisionMessage):
        if decision.id_instance > self.id_instance:
            self.d_val = [tup[0] for tup in decision.v_val]
            self.id_instance = decision.id_instance
            print(f"Learner {self.id} received decided value for {decision.id_instance} instace: {self.d_val}")

    def run(self):
        print(f"Learner {self.id} start...")
        while True:
            msg : bytes = self.r.recv(2**16)
            message : Message = pickle.loads(msg)
            if isinstance(message, DecisionMessage):
                self.receive_decision(message)

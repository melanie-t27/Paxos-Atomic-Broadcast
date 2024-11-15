from utils import *
from communication import *
from collections import defaultdict
import pickle

class Learner:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # Sockets
        self.r = mcast_receiver(config["learners"])
        # Decided value for each instance
        self.d_val : defaultdict[int,list[int]] = defaultdict(list)

    def receive_decision(self, decision : DecisionMessage):
        if decision.id_instance not in self.d_val.keys():
            self.d_val[decision.id_instance] = decision.v_val

    def run(self):
        while True:
            msg : bytes = self.r.recv(1024)
            message : Message = pickle.loads(msg)
            if isinstance(message, DecisionMessage):
                self.receive_decision(message)
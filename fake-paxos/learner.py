from utils import *
from communication import *
import pickle
import threading

class Learner:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # Sockets
        self.r = mcast_receiver(config["learners"])
        self.s = mcast_sender()
        # Decided value (each message is represented by its value and the client id that sent it) and related instance
        self.d_val : list[int] = list()
        self.id_instance = -1
        # Timer
        self.timer = threading.Timer(0.5, self.notify_proposer)
        self.timer.start()

    def receive_decision(self, decision : DecisionMessage):
        if decision.id_instance > self.id_instance:
            self.d_val = [tup[0] for tup in decision.v_val]
            self.id_instance = decision.id_instance
            print(f"Learner {self.id} received decided value for {decision.id_instance} instace: {self.d_val}")

    def notify_proposer(self):
        if d_val == list():
            print(f"Learner {self.id} notifies proposers...")
            message: LearnerMessage = LearnerMessage()
            self.s.sendto(pickle.dumps(message), self.config["proposers"])
            self.timer = threading.Timer(1, self.notify_proposer)
            self.timer.start()

    def run(self):
        print(f"Learner {self.id} start...")
        while True:
            msg : bytes = self.r.recv(2**16)
            message : Message = pickle.loads(msg)
            if isinstance(message, DecisionMessage):
                self.timer.cancel()
                self.receive_decision(message)

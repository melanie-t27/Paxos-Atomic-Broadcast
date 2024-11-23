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
        self.timer = threading.Timer(1, self.notify_proposer)
        self.timer.start()
        # Lock
        self.lock = threading.RLock()

    def receive_decision(self, decision : DecisionMessage):
        with self.lock:
            print(f"Learner {self.id} obtained decision at {decision.id_instance} while its instance is {self.id_instance}", flush=True)
            if decision.id_instance > self.id_instance:
                self.d_val = decision.v_val
                self.id_instance = decision.id_instance
                print(f"Learner {self.id} received decided value for {decision.id_instance} instace...")

    def notify_proposer(self):
        with self.lock:
            if self.d_val == list():
                print(f"Learner {self.id} notifies proposers...")
                message: LearnerArrivalMessage = LearnerArrivalMessage()
                self.s.sendto(pickle.dumps(message), self.config["proposers"])
                self.timer = threading.Timer(1, self.notify_proposer)
                self.timer.start()

    def run(self):
        print(f"Learner {self.id} start...", flush=True)
        while True:
            msg : bytes = self.r.recv(2**16)
            message : Message = pickle.loads(msg)
            print(f"Learner {self.id} received message {message}", flush=True)
            if isinstance(message, DecisionMessage):
                self.timer.cancel()
                self.receive_decision(message)

    def run_file(self, filename: str):
        print(f"Learner {self.id} start...", flush=True)
        while True:
            msg : bytes = self.r.recv(2**16)
            message : Message = pickle.loads(msg)
            print(f"Learner {self.id} received message {message}", flush=True)
            if isinstance(message, DecisionMessage):
                self.timer.cancel()
                self.receive_decision(message)
                # Clear the file by opening in write mode
                with open(filename, "w") as file:
                    for val in self.d_val:
                        file.write(f"{val}")


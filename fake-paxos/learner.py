from utils import *
from communication import *
import pickle
import threading
from collections import defaultdict

class Learner:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # Sockets
        self.r = mcast_receiver(config["learners"])
        self.s = mcast_sender()
        # Decided value (each message is represented by its value and the client id that sent it) and related instance
        self.d_val : defaultdict[int,list[int]] = defaultdict(list)
        # Missing id_instance
        self.missing_id_instance : int = 0
        # Last printed id_instance
        self.last_printed : int = -1
        # Timer
        self.timer = threading.Timer(1, self.notify_proposer)
        self.timer.start()
        # Lock
        self.lock = threading.RLock()

    def receive_decision(self, decision : DecisionMessage):
        with self.lock:
            if self.d_val[decision.id_instance] == list():
                self.timer.cancel()
                # Update decided value
                self.d_val[decision.id_instance] = decision.v_val
                # Update missing instance id
                while self.d_val[self.missing_id_instance] != list():
                    self.missing_id_instance += 1
                print(f"Learner {self.id} received decided value at {decision.id_instance}, send missing {self.missing_id_instance}", flush= True)
                self.notify_proposer()

    def notify_proposer(self):
        with self.lock:
            print(f"Learner {self.id} request proposers for {self.missing_id_instance}, since received {[key for key,l in self.d_val.items() if l != list()]}", flush = True)
            message: LearnerMessage = LearnerMessage(self.missing_id_instance)
            self.s.sendto(pickle.dumps(message), self.config["proposers"])
            self.timer = threading.Timer(1, self.notify_proposer)
            self.timer.start()

    def write_to_file(self, filename: str, id: int):
        current_id : int = id
        # If it is the first time the learner is printing, then open the file in write mode
        if current_id == 0 and self.d_val[0] != list() and self.last_printed == -1:
            with self.lock:
                with open(filename, "w") as file:
                    for val in self.d_val[current_id]:
                        file.write(f"{val}\n")
                self.last_printed = current_id
        # If it is not the first time the learner is printing, then append to the file,
        # also checks if there are still pending values to print
        while self.last_printed + 1 == current_id:
            if self.d_val[current_id] != list():
                with self.lock:
                    with open(filename, "a") as file:
                        for val in self.d_val[current_id]:
                            file.write(f"{val}\n")
                    self.last_printed = current_id
                    current_id += 1
            else:
                break

    def write(self, id : int):
        current_id : int = id
        # If it is the first time the learner is printing, then open the file in write mode
        if current_id == 0 and self.d_val[0] != list() and self.last_printed == -1:
            with self.lock:
                for val in self.d_val[current_id]:
                    print(f"{val}\n")
                self.last_printed = current_id
        # If it is not the first time the learner is printing, then append to the file,
        # also checks if there are still pending values to print
        while self.last_printed + 1 == current_id:
            if self.d_val[current_id] != list():
                with self.lock:
                    for val in self.d_val[current_id]:
                        print(f"{val}\n")
                    self.last_printed = current_id
                    current_id += 1
            else:
                break


    def run(self):
        print(f"Learner {self.id} start...", flush=True)
        while True:
            msg : bytes = self.r.recv(2**16)
            message : Message = pickle.loads(msg)
            if isinstance(message, DecisionMessage):
                self.receive_decision(message)
                self.write(message.id_instance)

    def run_file(self, filename: str):
        print(f"Learner {self.id} start...", flush=True)
        while True:
            msg : bytes = self.r.recv(2**16)
            message : Message = pickle.loads(msg)
            if isinstance(message, DecisionMessage):
                self.receive_decision(message)
                self.write_to_file(filename, message.id_instance)
            


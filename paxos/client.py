from communication import *
from messages import *
import pickle
import threading


class Client:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # Vector of all values 
        self.values : list[int] = list()
        # Socket
        self.s = mcast_sender()
        self.r = mcast_receiver(config["clients"])
        # Timer
        self.timer = threading.Timer(1, self.submit_values)
        self.timer.start()

    def submit_values(self):
        # Sends message to all proposers
        message : Message = ClientMessage(self.id, self.values)
        self.s.sendto(pickle.dumps(message), self.config["proposers"])
        # Restart timer
        self.timer = threading.Timer(1, self.submit_values)
        self.timer.start()
        
    
    def run(self):
        while True:
            try:
                value : str = input().strip()
                if not value:  # Check if input is empty
                    print("Empty input encountered.", flush=True)
                    continue
                try:
                    self.values.append(int(value))
                except:
                    print("Please submit an integer value.", flush=True)
            except EOFError:
                break
            
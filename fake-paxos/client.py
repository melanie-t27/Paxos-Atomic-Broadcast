from communication import *
from messages import *
import pickle
import time


class Client:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        # Vector of all values 
        self.values : list[int] = list()
        # Socket
        self.s = mcast_sender()

    def submit_values(self, values: list[int]):
        message : Message = ClientMessage(self.id, self.values)
        self.s.sendto(pickle.dumps(message), self.config["proposers"])
    
    def run(self):
        while True:
            value : str = input()
            if not value:
                break 
            try:
                self.values.append(int(value))
            except:
                print("Please submit an integer value.")

        while True:
            self.submit_values(self.values)
            time.sleep(1)
            


                 

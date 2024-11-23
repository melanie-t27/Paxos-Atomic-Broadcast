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
        print(f"Client {self.id} sends values to proposers..", flush=True)
        message : Message = ClientMessage(self.id, self.values)
        self.s.sendto(pickle.dumps(message), self.config["proposers"])
        # Restart timer
        self.timer = threading.Timer(1, self.submit_values)
        self.timer.start()
        
    
    def run(self):
        while True:
            value : str = input().strip()
            if not value:
                break 
            try:
                self.values.append(int(value))
            except:
                print("Please submit an integer value.")

        while True:
            msg = self.r.recv(2**16)
            message = pickle.loads(msg)
            if isinstance(message, NotifyClientMessage):
                if message.id_source == self.id:
                    # If the client receives a NotifyClientMessage then it means that its value
                    # have already been decided on, so it can stop sending them to the proposers
                    print(f"Client {self.id} stops sending messages after message of notify...", flush=True)
                    self.timer.cancel()


    def run_file(self, filename: str):
        print(f"Client {self.id} start...")
        try:
            with open(filename, 'r') as file:
                # Read all lines from the file
                for line in file:
                    # Strip any surrounding whitespace and attempt to convert to integer
                    try:
                        self.values.append(int(line.strip()))
                    except ValueError:
                        print(f"Warning: Skipping non-integer value: {line.strip()}")
        except FileNotFoundError:
            print(f"Error: The file '{filename}' was not found.")
        except ValueError as e:
            print(f"Error: Invalid data encountered. {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")  

        while True:
            msg = self.r.recv(2**16)
            message = pickle.loads(msg)
            if isinstance(message, NotifyClientMessage):
                if message.id_source == self.id:
                    # If the client receives a NotifyClientMessage then it means that its value
                    # have already been decided on, so it can stop sending them to the proposers
                    print(f"Client {self.id} stops sending messages after message of notify...", flush=True)
                    self.timer.cancel()

            
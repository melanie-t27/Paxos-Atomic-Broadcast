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
        #print(f"Client {self.id} sends values to proposers..", flush=True)
        message : Message = ClientMessage(self.id, self.values)
        self.s.sendto(pickle.dumps(message), self.config["proposers"])
        # Restart timer
        self.timer = threading.Timer(1, self.submit_values)
        self.timer.start()
        
    
    def run(self):
        print(f"Client {self.id} started...", flush = True)
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
                print("\nEOF encountered.", flush=True)
                break
            

    '''
        Method used just for testing purposes
    '''
    def run_file(self, filename: str):
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

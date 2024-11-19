from communication import *
from messages import *
import pickle
#import time


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
        
    
    '''def run(self):
        while True:
            value : str = input().strip()
            if not value:
                break 
            try:
                self.values.append(int(value))
            except:
                print("Please submit an integer value.")

        while True:
            self.submit_values(self.values)
            time.sleep(1)
    '''

    def run(self, filename: str):
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

        print(f"Client {self.id} sends values to proposers..")
        #while True:
        self.submit_values(self.values)
            #time.sleep(1)   
            
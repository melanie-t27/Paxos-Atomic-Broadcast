from abc import abstractmethod
from messages import*
from communication import *

# util function
def to_list_and_id(source: list[tuple[int,int]]) -> tuple[list[int], int]:
    if not source:
        # Handle the case where the input list is empty
        return ([], 0)
    # Extract the list of integers from each tuple's first element
    val : list[int] = [tup[0] for tup in source]
    # Extract the ID from the second element of the first tuple in the list, which is equal to all the other
    id : int = source[0][1]
    # Return a tuple: (list of integers, ID)
    return (val, id)

def from_list_and_id(val_and_id: tuple[list[int], int]) -> list[tuple[int, int]]:
    if not val_and_id:
        # Handle the case where the list of integers is empty
        return []
    # Unpack the tuple into the list and the integer
    val, id = val_and_id  
    # Create a list of tuples (v, id) for each integer v in val
    return [(v, id) for v in val]  

class State:
    @abstractmethod
    def on_event(self, event: Message):
        #Handle events that are delegated to this State.
        pass
    
    @abstractmethod
    def on_timeout(self):
        #Handle timeout for this State.
        pass
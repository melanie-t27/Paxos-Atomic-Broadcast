from abc import abstractmethod
from messages import*
from communication import *


class State:
    @abstractmethod
    def on_event(self, event: Message):
        #Handle events that are delegated to this State.
        pass
    
    @abstractmethod
    def on_timeout(self):
        #Handle timeout for this State.
        pass
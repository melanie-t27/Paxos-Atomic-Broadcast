from utils import *
import math
import threading
import pickle

class Proposer:
    def __init__(self, id: int, config: dict[str, tuple[str, int]], num_acceptors: int, num_proposers: int):
        self.id = id
        self.config = config
        self.quorum : int = math.ceil(num_acceptors / 2) 
        self.num_proposers = num_proposers
        self.round_responses: set[tuple[int,list[int]]] = set()
        self.id_instance = 0
        # Sockets
        self.r = mcast_receiver(config["proposers"])
        self.s = mcast_sender()
        # Obtained value from client
        self.v : list[int] = list()
        # Proposal round number (unique and increasing within proposers of the same paxos instance)
        self.c_rnd : int = id
        # Proposal value for this proposer picked at round proposal_round
        self.c_val : list[int] = list()
        # Decided value
        self.d_val :list[int] = list()
        # Lock
        self.lock = threading.RLock()
        # State machine 
        self.state : State = InitialState(self)

    def send_message(self, message : Message):
        if isinstance(message, Message1A) or isinstance(message, Message2A):
            self.s.sendto(pickle.dumps(message), self.config["acceptors"])
        elif isinstance(message, DecisionMessage):
            self.s.sendto(pickle.dumps(message), self.config["learners"])

    def handle_propose(self):
        # Increment the proposal number (acts as the round number) for each new proposal
        self.c_rnd = self.c_rnd + self.num_proposers
        # Send prepare messages to all acceptors
        msg : Message = Message1A(self.id, self.id_instance, self.c_rnd)
        self.send_message(msg)

    def handle_promise(self):
        k = max(t[0] for t in self.round_responses) 
        v = {t for t in self.round_responses if t[0] == k}
        if k == 0:
            self.c_val = self.v
        else:
            self.c_val = list(v)[0][1] # Get the second element of the tuple, they are all equal
        self.round_responses = set()
        msg: Message = Message2A(self.id, self.id_instance, self.c_rnd, self.c_val)
        self.send_message(msg)
                
    def handle_acceptance(self):
        # Prepare message with the right values
        msg: Message = DecisionMessage(self.id, self.id_instance, list(self.round_responses)[0][1])
        # Empty the messaged at the current round
        self.round_responses = set()
        # Send messages to all learners
        self.send_message(msg)
        # Save the decided value
        self.d_val.extend(list(self.round_responses)[0][1])
        # Delete the decided values from v 
        self.v = [value for value in self.v if value not in self.d_val] 
        # Update instance id
        self.id_instance += 1
                
    def set_state(self, state : State):
        self.state = state
    
    def run(self):
        state = InitialState(self)
        while True:
            msg = self.r.recv(1024)
            state.on_event(pickle.loads(msg))


########################## STATES FOR STATE MACHINE ##########################

class InitialState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()

    def on_event(self, event: Message):
        with self.proposer.lock:
            if isinstance(event, ClientMessage) and event.id_instance == self.proposer.id_instance:
                self.proposer.v.extend(value for value in event.values 
                                    if value not in self.proposer.v and value not in self.proposer.d_val) 
        
    def on_timeout(self):
        with self.proposer.lock:
            if self.proposer.v != list():
                self.proposer.set_state(Phase1AState(self.proposer))
            self.timer = threading.Timer(1, self.on_timeout)
            self.timer.start()
            
    
class Phase1AState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        # Sends message 1A to all acceptors
        self.proposer.handle_propose()
        # Start timer for message 1B arrival
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()
        

    def on_event(self, event: Message):
        # Wait for a quorum of messages 1B from the acceptors
        with self.proposer.lock:
            if isinstance(event, Message1B) and event.id_instance == self.proposer.id_instance:
                if event.rnd == self.proposer.c_rnd:
                    self.proposer.round_responses.add((event.v_rnd, event.v_val)) 
                    if len(self.proposer.round_responses) >= self.proposer.quorum:
                        self.proposer.set_state(Phase2AState(self.proposer))
    
    def on_timeout(self):
        with self.proposer.lock:
            # try another time to propose its values
            self.proposer.round_responses = set()
            self.proposer.handle_propose()
            self.timer = threading.Timer(1, self.on_timeout)
            self.timer.start()


class Phase2AState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        # Send message 2A to all acceptors
        self.proposer.handle_promise()
        # Set a timer for 2B message arrival
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()
        

    def check_quorum(self) -> bool:
        # Dictionary to count the occurrences of the first integer in each tuple
        count_dict : dict[int, int] = {}
        
        # Count occurrences of the first element (integer) in each tuple
        for t in self.proposer.round_responses:
            first_int = t[0]
            count_dict[first_int] = count_dict.get(first_int, 0) + 1
        
        # Find the first integer that appears at least `quorum` times
        for first_int, count in count_dict.items():
            if count >= self.proposer.quorum:
                # If found, filter `r` to keep only tuples with that first integer
                self.proposer.round_responses.intersection_update(
                    {t for t in self.proposer.round_responses if t[0] == first_int})
                return True
        return False


    def on_event(self, event: Message):
        # wait for a quorum of messages 2B from acceptors
        with self.proposer.lock:
            if isinstance(event, Message2B) and event.id_instance == self.proposer.id_instance:
                self.proposer.round_responses.add((event.v_rnd, event.v_val)) 
                if self.check_quorum():
                    self.proposer.set_state(Phase3State(self.proposer))
        
    def on_timeout(self):
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()
        

class Phase3State(State):
    # after sending the decision to the learner i need to increment instances
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        self.proposer.handle_acceptance()
        self.proposer.set_state(InitialState(self.proposer))

    def on_event(self, event: Message):
        pass
    
    def on_timeout(self):
        pass
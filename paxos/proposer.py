from utils import *
import math
import threading
import pickle
from collections import defaultdict

# We are assuming that there will be 3 acceptors
NUM_ACCEPTORS = 3




########################## PROPOSER IMPLEMENTED AS A FINITE STATE MACHINE ##########################
class Proposer:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        self.quorum : int = math.ceil(NUM_ACCEPTORS / 2) 
        # Lists to keep the acceptors responses at each phase
        self.round_responses_1B: list[tuple[int, tuple[tuple[int,int],...]]] = list()
        self.round_responses_2B: list[tuple[int, tuple[tuple[int,int],...]]] = list()
        # Current id instance of the poposer
        self.id_instance = 0
        # Sockets
        self.r = mcast_receiver(config["proposers"])
        self.s = mcast_sender()
        # Obtained value from client
        self.v : list[tuple[int,int]] = list()
        # Proposal round for this proposer for id_instance
        self.c_rnd : int = id
        # Proposal value for this proposer picked at round id_instance
        self.c_val : list[tuple[int,int]] = list()
        # Decided value
        self.d_val : defaultdict[int,list[tuple[int,int]]] = defaultdict(list)
        # Lock
        self.lock = threading.RLock()
        # State machine 
        self.state : State = InitialState(self)

    def send_message(self, message : Message):
        with self.lock:
            if isinstance(message, Message1A) or isinstance(message, Message2A):
                self.s.sendto(pickle.dumps(message), self.config["acceptors"])
            elif isinstance(message, DecisionMessage):
                self.s.sendto(pickle.dumps(message), self.config["learners"])

    def handle_propose(self):
        with self.lock:
            # Empty the lists
            self.round_responses_1B = list()
            self.round_responses_2B = list()
            # Increment the proposal number for each new proposal
            self.c_rnd = (self.c_rnd % 100) + (self.c_rnd // 100 + 1) * 100
            # Send prepare messages to all acceptors
            msg : Message = Message1A(self.id_instance, self.c_rnd)
            self.send_message(msg)

    def handle_promise(self):
        with self.lock:
            k = max(t[0] for t in self.round_responses_1B) 
            v = {t for t in self.round_responses_1B if t[0] == k}
            # Update the value according to the received 1B messages
            if k == 0:
                self.c_val = self.v
            else:
                self.c_val = list(list(v)[0][1]) # Get the second element of the tuple (the client id), they are all equal
            val, id = to_list_and_id(self.c_val)
            # Send messages 2A to all acceptors
            msg: Message = Message2A(self.id_instance, self.c_rnd, val, id)
            self.send_message(msg)

    def handle_acceptance(self):
        with self.lock:
            self.handle_change_of_instance(list(self.round_responses_2B[0][1]))
            val, _ = to_list_and_id(self.d_val[self.id_instance - 1])
            # Prepare message with the right values
            msg: Message = DecisionMessage(self.id_instance - 1, val)
            # Send messages to all learners
            self.send_message(msg)
        
    def handle_change_of_instance(self, v_val: list[tuple[int,int]]):
        with self.lock:
            # Save the decided value
            self.d_val[self.id_instance] = v_val
            # Remove all tuples with client id equal to the one decided
            client_id : int = v_val[0][1]
            self.v = [t for t in self.v if t[1] != client_id]
            # Update instance id
            self.id_instance += 1
            self.c_rnd = self.id

    def update_learners(self, id_instance: int):
        # Send messages to all learners, when one learner requests the decided values at a specific instance
        with self.lock:
            if self.d_val[id_instance] != list():
                val, _ = to_list_and_id(self.d_val[id_instance])
                # Send message to the learner
                msg: Message = DecisionMessage(id_instance, val)
                self.send_message(msg)


    def set_state(self, state : State):
        # Method to handle the change of state
        with self.lock:
            self.state = state
    
    def run(self):
        while True:
            msg = self.r.recv(2**16)
            message = pickle.loads(msg)
            with self.lock:
                if isinstance(message, LearnerMessage):
                    self.update_learners(message.id_instance)
                else: 
                    self.state.on_event(message)


########################## STATES FOR FINITE STATE MACHINE ##########################

class InitialState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()
        self.enable_timer : bool = True

    def on_event(self, event: Message):
        with self.proposer.lock:
            if isinstance(event, ClientMessage):
                # Update the values that still need to be proposed
                decided_values: set[tuple[int, int]] = {item for sublist in self.proposer.d_val.values() for item in sublist}
                existing_entries : set[tuple[int,int]] = set(self.proposer.v).union(decided_values)
                client_ids : set[int] = {t[1] for t in existing_entries}
                if event.id_source not in client_ids:
                    # Check if the new value are not already in the values to be proposed or in the values already decided
                    self.proposer.v.extend((value,event.id_source) for value in event.values)
                # If there are new values to propose, then start phase 1A
                if self.proposer.v != list():
                    self.timer.cancel()
                    self.enable_timer = False
                    self.proposer.set_state(Phase1AState(self.proposer))
        
    def on_timeout(self):
        with self.proposer.lock:
            if self.enable_timer == False:
                return
            # If there are values to propose, then go to phase 1A, otherwise keeps on waiting for new value to propose
            if self.proposer.v != list():
                self.timer.cancel()
                self.proposer.set_state(Phase1AState(self.proposer))
            else:
                # Restart timer if there are no new value
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
        self.enable_timer = True   

    def on_event(self, event: Message):
        # Wait for a quorum of messages 1B from the acceptors for the given instance
        with self.proposer.lock:
            if isinstance(event, Message1B):
                if event.rnd == self.proposer.c_rnd and event.id_instance == self.proposer.id_instance:
                    self.proposer.round_responses_1B.append((event.v_rnd, tuple(from_list_and_id((event.v_val, event.id_source))))) 
                    if len(self.proposer.round_responses_1B) >= self.proposer.quorum:
                        # If the quorum is achieved, then go to phase 2A
                        self.timer.cancel()
                        self.enable_timer = False
                        self.proposer.set_state(Phase2AState(self.proposer))
    
    def on_timeout(self):
        with self.proposer.lock:
            if self.enable_timer == False:
                return
            if self.proposer.v == list():
                self.timer.cancel()
                self.enable_timer = False
                self.proposer.set_state(InitialState(self.proposer))
            else:
                # Try another time to propose its values
                self.proposer.round_responses_1B = list()
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
        self.enable_timer = True
        

    def check_quorum(self) -> bool:
        with self.proposer.lock:
            # Dictionary to count the occurrences of the first integer in each tuple
            count_dict : dict[int, int] = {}
            
            # Count occurrences of the first element (integer) in each tuple
            for t in self.proposer.round_responses_2B:
                first_int = t[0]
                count_dict[first_int] = count_dict.get(first_int, 0) + 1
            
            # Find the first integer that appears at least `quorum` times
            for first_int, count in count_dict.items():
                if count >= self.proposer.quorum:
                    # If found, filter `self.proposer.round_responses_2B` to keep only tuples with that first integer
                    self.proposer.round_responses_2B = [
                        t for t in self.proposer.round_responses_2B if t[0] == first_int
                    ]
                    return True
            return False


    def on_event(self, event: Message):
        # wait for a quorum of messages 2B from acceptors
        with self.proposer.lock:
            if isinstance(event, Message2B) and event.id_instance == self.proposer.id_instance:
                self.proposer.round_responses_2B.append((event.v_rnd, tuple(from_list_and_id((event.v_val, event.id_source))))) 
                if self.check_quorum():
                    # Go to phase 3 (Decision)
                    self.timer.cancel()
                    self.enable_timer = False
                    self.proposer.set_state(Phase3State(self.proposer))
        
    def on_timeout(self):
        with self.proposer.lock:
            if self.enable_timer == False:
                return
            self.timer.cancel()
            self.proposer.handle_promise()
            self.timer = threading.Timer(1, self.on_timeout)
            self.timer.start()
        

class Phase3State(State):
    # after sending the decision to the learner i need to increment instances
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        self.proposer.handle_acceptance()
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()

    def on_event(self, event: Message):
        pass
    
    def on_timeout(self):
        with self.proposer.lock:
            self.timer.cancel()
            self.proposer.set_state(InitialState(self.proposer))
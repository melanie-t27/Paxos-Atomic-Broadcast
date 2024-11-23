from utils import *
import math
import threading
import pickle
import sys

# We are assuming that there will be 3 acceptors
NUM_ACCEPTORS = 3




########################## PROPOSER IMPLEMENTED AS A FINITE STATE MACHINE ##########################
class Proposer:
    def __init__(self, id: int, config: dict[str, tuple[str, int]]):
        self.id = id
        self.config = config
        self.quorum : int = math.ceil(NUM_ACCEPTORS / 2) 
        self.round_responses: list[tuple[int, tuple[tuple[int,int],...]]] = list()
        self.id_instance = 0
        # Sockets
        self.r = mcast_receiver(config["proposers"])
        self.s = mcast_sender()
        # Obtained value from client
        self.v : list[tuple[int,int]] = list()
        self.c_rnd : int = id
        # Proposal value for this proposer picked at round proposal_round
        self.c_val : list[tuple[int,int]] = list()
        # Decided value
        self.d_val :list[tuple[int,int]] = list()
        # Lock
        self.lock = threading.RLock()
        # State machine 
        self.state : State = InitialState(self)

    def send_message(self, message : Message):
        if isinstance(message, Message1A) or isinstance(message, Message2A):
            self.s.sendto(pickle.dumps(message), self.config["acceptors"])
        elif isinstance(message, DecisionMessage):
            self.s.sendto(pickle.dumps(message), self.config["learners"])
        elif isinstance(message, NotifyClientMessage):
            self.s.sendto(pickle.dumps(message), self.config["clients"])

    def handle_propose(self):
        # Increment the proposal number for each new proposal
        self.c_rnd = (self.c_rnd % 100) + (self.c_rnd // 100 + 1) * 100
        # Send prepare messages to all acceptors
        msg : Message = Message1A(self.id_instance, self.c_rnd)
        print(f"Proposer {self.id}({self.id_instance}) send proposal (size {sys.getsizeof(pickle.dumps(msg))}) with c-rnd = {self.c_rnd}", flush=True)
        self.send_message(msg)

    def handle_promise(self):
        k = max(t[0] for t in self.round_responses) 
        v = {t for t in self.round_responses if t[0] == k}
        if k == 0:
            self.c_val = self.v
        else:
            self.c_val = list(list(v)[0][1]) # Get the second element of the tuple, they are all equal
        self.round_responses = list()
        val, id = to_list_and_id(self.c_val)
        msg: Message = Message2A(self.id_instance, self.c_rnd, val, id)
        print(f"Proposer {self.id}({self.id_instance}) sends 2A (size {sys.getsizeof(pickle.dumps(msg))}): c_rnd = {self.c_rnd}", flush=True)
        self.send_message(msg)

    def handle_acceptance(self):
        self.handle_change_of_instance(list(self.round_responses[0][1]))
        id_client : int = self.d_val[len(self.d_val)-1][1]
        val, _ = to_list_and_id(self.d_val)
        # Prepare message with the right values
        msg: Message = DecisionMessage(self.id_instance, val)
        print(f"Proposer {self.id}({self.id_instance}) sends decision message (size {sys.getsizeof(pickle.dumps(msg))}) to learners and message to client {id_client}", flush=True)
        # Send messages to all learners
        self.send_message(msg)
        # Send message to the client so that it can stop sending its value
        msg1: Message = NotifyClientMessage(id_client)
        # Send messages to all learners
        self.send_message(msg1)
        
    def handle_change_of_instance(self, v_val: list[tuple[int,int]]):
        # Save the decided value
        self.d_val.extend(v_val)
        # Delete the decided values from v 
        self.v = [value for value in self.v if value not in self.d_val] 
        # Update instance id
        self.id_instance += 1
        self.c_rnd = self.id
        # Empty the messaged at the current round
        self.round_responses = list()

    def update_learners(self):
        # Send messages to all learners
        with self.lock:
            val, _ = to_list_and_id(self.d_val)
            msg: Message = DecisionMessage(self.id_instance - 1, val)
            self.send_message(msg)
       
    def set_state(self, state : State):
        self.state = state
    
    def run(self):
        print(f"Proposer {self.id} start...", flush=True)
        while True:
            msg = self.r.recv(2**16)
            message = pickle.loads(msg)
            if isinstance(message, LearnerArrivalMessage):
                print(f"Proposer {self.id} received learner arrival message and sends update to learners", flush=True)
                self.update_learners()
            else: 
                self.state.on_event(message)


########################## STATES FOR FINITE STATE MACHINE ##########################

class InitialState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()
        print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) waiting for client messages...", flush=True)

    def on_event(self, event: Message):
        with self.proposer.lock:
            if isinstance(event, ClientMessage):
                # Create a set for faster membership checks
                existing_entries : set[tuple[int,int]] = set(self.proposer.v).union(self.proposer.d_val)
                # Check if the new value are not already in the values to be proposed or in the values already decided
                self.proposer.v.extend((value,event.id_source) for value in event.values 
                                    if (value, event.id_source) not in existing_entries) 
                if self.proposer.v != list():
                    self.timer.cancel()
                    print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) received client {event.id_source} messages and start phase 1A", flush=True)
                    self.proposer.set_state(Phase1AState(self.proposer))
        
    def on_timeout(self):
        with self.proposer.lock:
            print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) timeout in initial phase", flush=True)
            if self.proposer.v:
                self.timer.cancel()
                self.proposer.set_state(Phase1AState(self.proposer))
            self.timer = threading.Timer(1, self.on_timeout)
            self.timer.start()
            
    
class Phase1AState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        # Sends message 1A to all acceptors
        self.proposer.handle_propose()
        print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) waiting for 1B messages...", flush=True)
        # Start timer for message 1B arrival
        self.timer = threading.Timer(1, self.on_timeout)
        self.timer.start()      

    def on_event(self, event: Message):
        # Wait for a quorum of messages 1B from the acceptors
        with self.proposer.lock:
            if isinstance(event, Message1B):
                if event.rnd == self.proposer.c_rnd and event.id_instance == self.proposer.id_instance:
                    self.proposer.round_responses.append((event.v_rnd, tuple(from_list_and_id((event.v_val, event.id_source))))) 
                    print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) received a 1B message, waiting for quorum (len set = {len(self.proposer.round_responses)})", flush=True)
                    if len(self.proposer.round_responses) >= self.proposer.quorum:
                        print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) received a quorum of 1B messages and changes state to 2A...", flush=True)
                        self.timer.cancel()
                        self.proposer.set_state(Phase2AState(self.proposer))
    
    def on_timeout(self):
        with self.proposer.lock:
            print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) timeout in phase 1A", flush=True)
            # try another time to propose its values
            self.proposer.round_responses = list()
            self.proposer.handle_propose()
            self.timer = threading.Timer(1, self.on_timeout)
            self.timer.start()


class Phase2AState(State):
    def __init__(self, proposer: Proposer):
        self.proposer = proposer
        # Send message 2A to all acceptors
        self.proposer.handle_promise()
        print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) waiting for 2B messages...", flush=True)
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
                # If found, filter `self.proposer.round_responses` to keep only tuples with that first integer
                self.proposer.round_responses = [
                    t for t in self.proposer.round_responses if t[0] == first_int
                ]
                return True
        return False


    def on_event(self, event: Message):
        # wait for a quorum of messages 2B from acceptors
        with self.proposer.lock:
            if isinstance(event, Message2B) and event.id_instance == self.proposer.id_instance:
                self.proposer.round_responses.append((event.v_rnd, tuple(from_list_and_id((event.v_val, event.id_source))))) 
                if self.check_quorum():
                    print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) received a quorum of 2B messages", flush=True)
                    self.timer.cancel()
                    print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) changing state to 3...", flush=True)
                    self.proposer.set_state(Phase3State(self.proposer))
        
    def on_timeout(self):
        with self.proposer.lock:
            print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) timeout in phase 2A", flush=True)
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
            print(f"Proposer {self.proposer.id}({self.proposer.id_instance}) changing state to initial after sending decision...", flush=True)
            self.proposer.set_state(InitialState(self.proposer))
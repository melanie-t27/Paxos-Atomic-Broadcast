import threading
from proposer import *
from acceptor import *
from learner import *
from client import *
import time

if __name__ == "__main__":
    config : dict[str, tuple[str,int]] = {}
    config["clients"] = ("239.0.0.1", 5000)
    config["proposers"] = ("239.0.0.1", 6000)
    config["acceptors"] = ("239.0.0.1", 7000)
    config["learners"] = ("239.0.0.1", 8000)

    client1 = Client(1, config)
    client2 = Client(2, config)
    proposer1 = Proposer(1, config)
    #proposer2 = Proposer(2, config)
    learner1 = Learner(1, config)
    learner2 = Learner(2, config)
    acceptor1 = Acceptor(1, config)
    acceptor2 = Acceptor(2, config)
    acceptor3 = Acceptor(3, config)

    threading.Thread(target = client1.run, args=["test1_5"]).start()
    threading.Thread(target = client2.run, args=["test2_5"]).start()
    threading.Thread(target = learner1.run).start()
    threading.Thread(target = learner2.run).start()
    threading.Thread(target = proposer1.run).start()
    #threading.Thread(target = proposer2.run).start()
    threading.Thread(target = acceptor1.run).start()
    threading.Thread(target = acceptor2.run).start()
    threading.Thread(target = acceptor3.run).start()
    time.sleep(10)
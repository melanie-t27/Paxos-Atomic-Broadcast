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

    client = Client(1, config)
    proposer = Proposer(1, config)
    learner = Learner(1, config)
    acceptor1 = Acceptor(1, config)
    acceptor2 = Acceptor(2, config)
    acceptor3 = Acceptor(3, config)

    threading.Thread(target = client.run, args=["test_input"]).start()
    threading.Thread(target = learner.run).start()
    threading.Thread(target = proposer.run).start()
    threading.Thread(target = acceptor1.run).start()
    threading.Thread(target = acceptor2.run).start()
    threading.Thread(target = acceptor3.run).start()
    time.sleep(10)
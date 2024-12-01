import threading
from proposer import *
from acceptor import *
from learner import *
from client import *
import time
import argparse

if __name__ == "__main__":
    # Parse the command-line argument for x
    parser = argparse.ArgumentParser(description="Run Paxos simulation.")
    parser.add_argument("x", type=int, choices=[5, 100, 1000], help="The value of x for the input file path")
    args = parser.parse_args()
    x = args.x

    config : dict[str, tuple[str,int]] = {}
    config["clients"] = ("239.0.0.1", 5000)
    config["proposers"] = ("239.0.0.1", 6000)
    config["acceptors"] = ("239.0.0.1", 7000)
    config["learners"] = ("239.0.0.1", 8000)
    
    #proposer2 = Proposer(2, config)
    #threading.Thread(target = proposer2.run).start()
    
    client1 = Client(1, config)
    threading.Thread(target = client1.run_file, args=[f"input_tests/test1_{x}"]).start()

    client2 = Client(2, config)
    threading.Thread(target = client2.run_file, args=[f"input_tests/test2_{x}"]).start()

    learner1 = Learner(1, config)
    threading.Thread(target = learner1.run_file, args=["output1.txt"]).start()

    proposer1 = Proposer(1, config)
    threading.Thread(target = proposer1.run).start()
    

    acceptor1 = Acceptor(1, config)
    threading.Thread(target = acceptor1.run).start()

    acceptor2 = Acceptor(2, config)
    threading.Thread(target = acceptor2.run).start()

    acceptor3 = Acceptor(3, config)
    threading.Thread(target = acceptor3.run).start()

    time.sleep(10)
    client3 = Client(3, config)
    threading.Thread(target = client3.run_file, args=[f"input_tests/test1_{x}"]).start()

    time.sleep(10)
    learner2 = Learner(2, config)
    threading.Thread(target = learner2.run_file, args=["output2.txt"]).start()

    time.sleep(60)
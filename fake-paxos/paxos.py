#!/usr/bin/env python3

from participants import *


def parse_cfg(cfgpath : str):
    cfg : dict[str, tuple[str, int]] = {}
    with open(cfgpath, "r") as cfgfile:
        for line in cfgfile:
            (role, host, port) = line.split()
            cfg[role] = (host, int(port))
    return cfg


# ----------------------------------------------------

'''
def acceptor(config : dict[str, tuple[str, int]], id : int):
    print("-> acceptor", id)
    state = {}
    r = mcast_receiver(config["acceptors"])
    s = mcast_sender()
    while True:
        msg = r.recv(2**16)
        # fake acceptor! just forwards messages to the learner
        if id == 1:
            print("acceptor: sending %s to learners", msg) 
            s.sendto(msg, config["learners"])


def proposer(config, id):
    print("-> proposer", id)
    r = mcast_receiver(config["proposers"])
    s = mcast_sender()
    while True:
        print("Proposer ", id, " waiting...")
        msg = r.recv(2**16)
        # fake proposer! just forwards message to the acceptor
        if id == 1:
            print("proposer: sending %s to acceptors", (msg))
            
            s.sendto(msg, config["acceptors"])


def learner(config, id):
    print("-> learner", id)
    r = mcast_receiver(config["learners"])
    while True:
        msg = r.recv(2**16)
        print(msg)
        sys.stdout.flush()


def client(config, id):
    print("-> client ", id)
    s = mcast_sender()
    for value in sys.stdin:
        value = value.strip()
        print("client: sending %s to proposers" % (value))
        s.sendto(value.encode(), config["proposers"])
    print("client done.")
'''
'''
if __name__ == "__main__":
    cfgpath = sys.argv[1]
    config = parse_cfg(cfgpath)
    role = sys.argv[2]
    id = int(sys.argv[3])
    if role == "acceptor":
        rolefunc = Acceptor
    elif role == "proposer":
        rolefunc = Proposer
    elif role == "learner":
        rolefunc = Learner
    elif role == "client":
        rolefunc = Client
    rolefunc(config, id)
'''

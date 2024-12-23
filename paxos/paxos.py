#!/usr/bin/env python3

from learner import *
from acceptor import *
from client import *
from proposer import *
import sys


def parse_cfg(cfgpath : str):
    cfg : dict[str, tuple[str, int]] = {}
    with open(cfgpath, "r") as cfgfile:
        for line in cfgfile:
            (role, host, port) = line.split()
            cfg[role] = (host, int(port))
    return cfg


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
    else:
        raise Exception("Invalid input!")
    participant = rolefunc(id, config)
    participant.run()

"""
CSEE4119 Programming Assignment2
Author: Jing Tang
Date: 2022.04.21
Main function: read the input and determine which mode it is
"""

import socket
import threading
import os
import sys
from distanceVector import *
from linkState import *

if __name__ == '__main__':
    alg = sys.argv[1]
    last = 0
    change = -1
    lastneigh = None
    if alg == "dv":
        neigh = {}
        model = sys.argv[2]
        src = int(sys.argv[4])
        lens = len(sys.argv)
        for i in range(5, len(sys.argv)-1, 2):
            if sys.argv[i] != "last":
                neigh[int(sys.argv[i])] = int(sys.argv[i+1])
        if sys.argv[-1] == "last" or sys.argv[-2] == "last":
            last = 1
            if sys.argv[-1] != "last":
                change = int(sys.argv[-1])
                lastneigh = int(sys.argv[-4])
        initRouter(model, src, neigh, last, change, lastneigh)
    if alg == "ls":
        neigh = {}
        model = sys.argv[2]
        src = int(sys.argv[4])
        update_interval = int(sys.argv[3])
        lens = len(sys.argv)
        for i in range(5, len(sys.argv) - 1, 2):
            if sys.argv[i] != "last":
                neigh[int(sys.argv[i])] = int(sys.argv[i + 1])
        if sys.argv[-1] == "last" or sys.argv[-2] == "last":
            last = 1
            if sys.argv[-1] != "last":
                change = int(sys.argv[-1])
                lastneigh = int(sys.argv[-4])
        initLinkState(model, src, neigh, last, change, lastneigh, update_interval)

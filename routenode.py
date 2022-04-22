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

if __name__ == '__main__':
    alg = sys.argv[1]
    last = 0
    change = 0
    if alg == "dv":
        neigh = {}
        model = sys.argv[2]
        src = sys.argv[4]
        lens = len(sys.argv)
        for i in range(5, len(sys.argv), 2):
            if sys.argv[i] != "last":
                neigh[sys.argv[i]] = sys.argv[i+1]
            else:
                last = 1
                if sys.argv[-1] != "last":
                    change = sys.argv[-1]

        if last == 0:
            initRouter(model, src, neigh, last)

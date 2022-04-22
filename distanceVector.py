"""
CSEE4119 Programming Assignment2
Author: Jing Tang
Date: 2022.04.21

Distance Algorithm Routing Algorithm
"""

import socket
import sys
import os
import time
from routenode import *

class Router():
    graph = {}
    shortest_path = {}
    neighbour = []
    last = 0

    def __init__(self, model, src, neigh):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.src = src
        self.model = model
        for key in neigh:
            self.neighbour.append(key)
        self.graph[src] = neigh

    def bellman_ford(self):
        rec = {}
        p = {}
        infinity = float("inf")
        for v in self.graph:
            rec[v] = infinity
            p[v] = None
        rec[self.src] = 0

        for i in range(len(self.graph) - 1):
            for u in self.graph:
                for v in self.graph[u]:
                    if rec[v] > self.graph[u][v] + rec[u]:
                        rec[v] = self.graph[u][v] + rec[u]
                        p[v] = u

        # check if a cycle existed
        for u in self.graph:
            for v in self.graph[u]:
                if rec[v] > rec[u] + self.graph[u][v]:
                    return None, None

        return rec, p


def initRouter(model, src, neigh, last):
    router = Router(model, src, neigh)

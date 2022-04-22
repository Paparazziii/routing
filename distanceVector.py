"""
CSEE4119 Programming Assignment2
Author: Jing Tang
Date: 2022.04.21

Distance Algorithm Routing Algorithm
"""

import socket
import sys, json
import os
import time
from routenode import *


class Router():
    graph = {}  # key is all other routers, value is their router table
    neighbour = []
    last = 0
    changed = 1

    def __init__(self, model, src, neigh):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.src = src
        self.servP = (self.ip, src)
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind(self.servP)
        self.model = model
        self.router_table = {self.src:[0,None,0]}  # key is all routers, value is [shortest path, next-hop, isneighbour]
        for key in neigh:
            self.neighbour.append(int(key))
            self.router_table[int(key)] = [neigh[key], None, 1]
            self.graph[int(key)] = {}

    def recv(self):
        while True:
            data, srcAddr = self.udpSocket.recvfrom(1024)
            loaded = json.loads(data.decode())
            types = loaded["type"]
            info = loaded["info"]
            ip, srcPort = srcAddr
            print(f"[{time.time()}] Message received at Node {self.src} from Node {srcPort}")
            newTable = {}
            for key in info:
                newTable[int(key)] = info[key]
            if types == "updatecost":
                self.updatecost(srcAddr, newTable)

    def bellman_ford(self, rec):
        infinity = float("inf")
        changed = 0
        #rec = self.router_table
        #rec[self.src] = [0, None, 0]
        # self.router_table[self.src] = [0, None, 0]
        for v in self.graph:
            if v not in rec:
                rec[v] = [infinity, None, 0]

        for dest in self.graph:
            #if dest != rec:
            for nb in self.neighbour:
                if dest in self.graph[nb]:
                    d = self.graph[nb][dest][0] + rec[nb][0]
                    if d < rec[dest][0]:
                        changed = 1
                        rec[dest][0] = d
                        rec[dest][1] = nb
        return rec, changed

    def updatecost(self, srcAddr, info):
        ip, srcPort = srcAddr
        srcPort = int(srcPort)
        checksrc = self.src
        if info[checksrc][2] == 1:
            if srcPort not in self.neighbour:
                self.neighbour.append(srcPort)
                self.router_table[srcPort] = [info[checksrc][0], None, 1]
                self.graph[srcPort] = info
        for key in info:
            if key not in self.graph:
                self.graph[key] = {srcPort:[info[key][0], srcPort, info[key][2]]}
            elif srcPort not in self.graph[key]:
                self.graph[key][srcPort] = [info[key][0], srcPort, info[key][2]]
        if srcPort not in self.graph or self.graph[srcPort] != info:
            self.graph[srcPort] = info
            originRT = self.router_table
            rec, changed = self.bellman_ford(originRT)
            self.changed = self.changed|changed
            if self.changed == 1:
                self.router_table = rec
                self.broadcast()
                self.changed = 0
                self.showtable()

    def showtable(self):
        print(f"[{time.time()}] Node {self.src} Routing Table")
        for i in sorted(self.router_table.keys()):
            if i != self.src:
                if self.router_table[i][1] is None:
                    print(f"- ({self.router_table[i][0]}) -> Node {i}")
                else:
                    print(f"- ({self.router_table[i][0]}) -> Node {i}; "
                        f"Next hop -> Node {self.router_table[i][1]}")

    def broadcast(self):
        for key in self.neighbour:
            addr = (self.ip, key)
            data = {'type': "updatecost", 'info': self.router_table}
            self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
            print(f"[{time.time()}] Message sent from Node {self.src} to Node {key}")

def initRouter(model, src, neigh, last):
    try:
        router = Router(model, src, neigh)
        if last == 1:
            router.broadcast()
        router.recv()
    except KeyboardInterrupt:
        print("Exiting")

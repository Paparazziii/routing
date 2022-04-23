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

    def __init__(self, model, src, neigh, last, change, lastneigh, init_time):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.src = src
        self.servP = (self.ip, src)
        self.initTime = init_time
        self.last = 0
        #print(f"CHANGE = {change}")
        if last == 1 and change != -1 and model == 'r':
            self.last = last
            self.changeBit = change
            self.model = model
            self.lastNeigh = lastneigh
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
            currTime = time.time()
            print(f"LAST = {self.last}")
            print(f"MODE = {self.model}")
            if self.last == 1 and self.model == 'r':
                print(currTime - self.initTime)
                if currTime - self.initTime >= 30:
                    addr = (self.ip, self.lastNeigh)
                    data = {'type': "linkchange", 'info': self.router_table}
                    print(f"[{time.time()}] Node {self.lastNeigh} cost updated to self.changeBit")
                    self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
                    print(f"[{time.time()}] Link value message sent from Node {self.src} to Node {self.lastNeigh}")
                    #self.router_table[self.lastNeigh] = [change, None, 1]
                    self.graph[self.src][self.lastNeigh] = [self.changeBit, None, 1]
                    self.graph[self.lastNeigh][self.src] = [self.changeBit, None, 1]
                    rec, changed = self.bellman_ford(self.graph)
                    if changed:
                        self.router_table = rec
                        self.broadcast("updatecost")
                        self.showtable()
            data, srcAddr = self.udpSocket.recvfrom(1024)
            loaded = json.loads(data.decode())
            types = loaded["type"]
            info = loaded["info"]
            ip, srcPort = srcAddr
            if types == "updatecost":
                print(f"[{time.time()}] Message received at Node {self.src} from Node {srcPort}")
            if types == "linkchange":
                print(f"[{time.time()}] Link value message received at Node {self.src} from Node {srcPort}")
            newTable = {}
            for key in info:
                newTable[int(key)] = info[key]
            if types == "updatecost":
                self.updatecost(srcAddr, newTable)

    def bellman_ford(self, rec):
        infinity = float("inf")
        changed = 0
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
                self.broadcast("updatecost")
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

    def broadcast(self, type):
        for key in self.neighbour:
            addr = (self.ip, key)
            data = {'type': type, 'info': self.router_table}
            self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
            print(f"[{time.time()}] Message sent from Node {self.src} to Node {key}")


def initRouter(model, src, neigh, last, change, lastneigh):
    try:
        init_time = time.time()
        router = Router(model, src, neigh, last, change, lastneigh, init_time)
        if last == 1:
            router.broadcast("updatecost")
        router.recv()
    except KeyboardInterrupt:
        print("Exiting")

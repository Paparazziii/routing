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
from threading import Thread


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
        self.last = last
        self.changeBit = change
        self.lastNeigh = lastneigh
        self.model = model
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind(self.servP)
        self.model = model
        self.router_table = {self.src:[0,None,0]}  # key is all routers, value is [shortest path, next-hop, isneighbour]
        for key in neigh:
            self.neighbour.append(int(key))
            self.router_table[int(key)] = [neigh[key], None, 1]
            self.graph[int(key)] = {}
        self.Thread_recv = Thread(target=self.recv)
        self.Thread_waiter = Thread(target=self.timewaiter)

    def start(self):
        try:
            self.Thread_recv.daemon = True
            self.Thread_waiter.daemon = True
            self.Thread_recv.start()
            self.Thread_waiter.start()
            while self.Thread_recv.isAlive():
                self.Thread_recv.join(1)
            while self.Thread_waiter.isAlive():
                self.Thread_waiter.join(1)
        except (KeyboardInterrupt, SystemExit):
            print("Exiting")
            sys.exit()

    def recv(self):
        while True:
            data, srcAddr = self.udpSocket.recvfrom(1024)
            loaded = json.loads(data.decode())
            types = loaded["type"]
            info = loaded["info"]
            ip, srcPort = srcAddr
            if types == "updatecost":
                print(f"[{time.time()}] Message received at Node {self.src} from Node {srcPort}")
                newTable = {}
                for key in info:
                    newTable[int(key)] = info[key]
                #print(f"SRC {srcPort}  {newTable}")
                self.updatecost(srcAddr, newTable)
            if types == "linkchange":
                print(f"[{time.time()}] Link value message received at Node {self.src} from Node {srcPort}")
                changebit = info
                print(f"[{time.time()}] Node {srcPort} cost updated to {changebit}")
                self.graph[self.src][srcPort] = [changebit, None, 1]
                self.graph[srcPort][self.src] = [changebit, None, 1]
                thechange = 0
                if self.router_table[srcPort][0] != changebit:
                    self.router_table[srcPort] = [changebit, None, 1]
                    thechange = 1
                #print(f"BEFORE {self.router_table}")
                rec, changed = self.bellman_ford(self.router_table)
                #print(f"AFTER {rec}")
                if changed|thechange:
                    self.router_table = rec
                    self.broadcast("updatecost")
                    self.showtable()

    def timewaiter(self):
        while True:
            if self.last == 1 and self.changeBit != -1:
                print("Start Waiting")
                time.sleep(10)
                addr = (self.ip, self.lastNeigh)
                data = {'type': "linkchange", 'info': self.changeBit}
                print(f"[{time.time()}] Node {self.lastNeigh} cost updated to {self.changeBit}")
                self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
                print(f"[{time.time()}] Link value message sent from Node {self.src} to Node {self.lastNeigh}")
                # self.router_table[self.lastNeigh] = [change, None, 1]
                self.graph[self.src][self.lastNeigh] = [self.changeBit, None, 1]
                self.graph[self.lastNeigh][self.src] = [self.changeBit, None, 1]        
                self.router_table[self.lastNeigh] = [self.changeBit, None, 1]
                rec, changed = self.bellman_ford(self.router_table)
                if changed:
                    self.router_table = rec
                    self.broadcast("updatecost")
                    self.showtable()
                break

    def bellman_ford(self, rec):
        infinity = float("inf")
        changed = 0
        print(f"REC {rec}")
        for dest in self.graph:
            if dest != self.src:
                cost = infinity
                nexthop = None
                for nb in self.neighbour:
                    if dest in self.graph[nb]:
                        d = self.graph[nb][dest][0] + rec[nb][0]
                        if d < cost:
                            cost = d
                            nexthop = nb
                if cost != rec[dest][0]:
                    changed = 1
                    rec[dest][0] = cost
                    rec[dest][1] = nexthop
                    print(f"after {rec}")
        """
        for v in self.graph:
            if v not in rec:
                rec[v] = [infinity, None, 0]

        for dest in self.graph:
            #if dest != rec:
            for nb in self.neighbour:
                if dest in self.graph[nb]:
                    d = self.graph[nb][dest][0] + rec[nb][0]
                    #d = infinity
                    #print(f"GRAPH  {self.graph[nb][dest][0]}")
                    #print(f"TABLE  {rec[nb]}")
                    if d < rec[dest][0]:
                        changed = 1
                        rec[dest][0] = d
                        rec[dest][1] = nb
        """
        return rec, changed

    def updatecost(self, srcAddr, info):
        ip, srcPort = srcAddr
        srcPort = int(srcPort)
        checksrc = self.src
        if info[checksrc][2] == 1:
            #print("111111111111111111111111111")
            if srcPort not in self.neighbour:
                #print("222222222222222222222")
                self.neighbour.append(srcPort)
                self.router_table[srcPort] = [info[checksrc][0], None, 1]
                self.graph[srcPort] = info
        for key in info:
            if key not in self.graph:
                #print("2222222222222222222")
                self.graph[key] = {srcPort:[info[key][0], srcPort, info[key][2]]}
            elif srcPort not in self.graph[key]:
                #print("333333333333333333333")
                self.graph[key][srcPort] = [info[key][0], srcPort, info[key][2]]
        if srcPort not in self.graph or self.graph[srcPort] != info:
            #print("444444444444444444444")
            #print(self.graph[srcPort])
            #print(info)
            #print(self.router_table)
            self.graph[srcPort] = info
            originRT = self.router_table
            rec, changed = self.bellman_ford(originRT)
            self.changed = self.changed|changed
            if self.changed == 1:
                #print("555555555555555555")
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
        router.start()
    except KeyboardInterrupt:
        print("Exiting")

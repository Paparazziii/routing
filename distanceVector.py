"""
CSEE4119 Programming Assignment2
Author: Jing Tang
Date: 2022.04.21

Distance Algorithm Routing Algorithm
"""

import socket
import sys
import json
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
        self.neighbour = {}
        self.router_table = {self.src:[0,None,0]}  # key is all routers, value is [shortest path, next-hop, isneighbour]
        for key in neigh:
            self.neighbour[int(key)] = neigh[key]
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

    # receive the router table updating from other routers
    def recv(self):
        while True:
            data, srcAddr = self.udpSocket.recvfrom(1024)
            loaded = json.loads(data.decode())
            types = loaded["type"]
            info = loaded["info"]
            ip, srcPort = srcAddr
            threadtask = Thread(target=self.dealWithInput, args=[types, info, srcPort, srcAddr])
            threadtask.setDaemon(True)
            threadtask.start()
            #threadtask.join()

    # if there's a link change, wait for 30s and send new link to the other end
    def timewaiter(self):
        while True:
            # check condition
            if self.last == 1 and self.changeBit != -1:
                print(f"[{time.time()}] Start Waiting For Link Change")
                # wait for 30 seconds
                time.sleep(30)
                addr = (self.ip, self.lastNeigh)
                data = {'type': "linkchange", 'info': self.changeBit}
                print(f"[{time.time()}] Node {self.lastNeigh} cost updated to {self.changeBit}")
                self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
                print(f"[{time.time()}] Link value message sent from Node {self.src} to Node {self.lastNeigh}")
                # self.router_table[self.lastNeigh] = [change, None, 1]
                self.graph[self.src][self.lastNeigh] = [self.changeBit, None, 1]
                self.graph[self.lastNeigh][self.src] = [self.changeBit, None, 1]        
                self.router_table[self.lastNeigh] = [self.changeBit, None, 1]
                self.neighbour[self.lastNeigh] = self.changeBit
                rec, changed = self.bellman_ford(self.router_table)
                if changed:
                    self.router_table = rec
                    self.broadcast("updatelinkcost", self.router_table)
                    self.showtable()
                break

    def dealWithInput(self, types, info, srcPort, srcAddr):
        if types == "updatecost":
            print(f"[{time.time()}] Message received at Node {self.src} from Node {srcPort}")
            newTable = {}
            for key in info:
                newTable[int(key)] = info[key]
            # check if the router table need to be updated
            self.updatecost(srcAddr, newTable)
        # receive link change info
        elif types == "linkchange":
            print(f"[{time.time()}] Link value message received at Node {self.src} from Node {srcPort}")
            changebit = info
            print(f"[{time.time()}] Node {srcPort} cost updated to {changebit}")
            # modify the graph with new link
            self.graph[self.src][srcPort] = [changebit, None, 1]
            self.graph[srcPort][self.src] = [changebit, None, 1]
            self.neighbour[srcPort] = changebit
            thechange = 0
            if self.router_table[srcPort][0] != changebit:
                self.router_table[srcPort] = [changebit, None, 1]
                thechange = 1
            # update the router table through bellman-ford alg
            rec, changed = self.bellman_ford(self.router_table)
            # if router table changed, broadcast to all neighbours
            if changed | thechange:
                self.router_table = rec
                self.broadcast("updatecost", self.router_table)
                self.showtable()

    def bellman_ford(self, rec):
        infinity = float("inf")
        changed = 0
        for dest in self.graph:
            if dest != self.src:
                cost = infinity
                nexthop = None
                if dest in self.neighbour:
                    cost = self.neighbour[dest]
                for nb in self.neighbour:
                    if dest in self.graph[nb] and dest != nb:
                        d = self.graph[nb][dest][0] + rec[nb][0]
                        if d < cost:
                            cost = d
                            nexthop = nb
                if cost != rec[dest][0]:
                    changed = 1
                    rec[dest][0] = cost
                    rec[dest][1] = nexthop

        return rec, changed

    def updatecost(self, srcAddr, info):
        ip, srcPort = srcAddr
        srcPort = int(srcPort)
        checksrc = self.src
        if info[checksrc][2] == 1:
            if srcPort not in self.neighbour:
                self.neighbour[srcPort] = info[checksrc][0]
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
            if self.changed == 1 and self.model == "r":
                self.router_table = rec
                self.broadcast("updatecost", self.router_table)
                self.changed = 0
                self.showtable()
            elif self.changed == 1 and self.model == "p":
                self.router_table = rec
                self.showtable()
                self.poisonReverse("updatecost", self.router_table)
                self.changed = 0

    def showtable(self):
        print(f"[{time.time()}] Node {self.src} Routing Table")
        for i in sorted(self.router_table.keys()):
            if i != self.src:
                if self.router_table[i][1] is None:
                    print(f"- ({self.router_table[i][0]}) -> Node {i}")
                else:
                    print(f"- ({self.router_table[i][0]}) -> Node {i}; "
                        f"Next hop -> Node {self.router_table[i][1]}")

    def broadcast(self, type, table):
        for key in self.neighbour:
            addr = (self.ip, key)
            data = {'type': type, 'info': table}
            self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
            print(f"[{time.time()}] Message sent from Node {self.src} to Node {key}")

    def poisonReverse(self, type, table):
        poison = []
        newTable = self.router_table
        for dest in self.graph:
            for key in self.neighbour:
                addr = (self.ip, key)
                data = {'type': "updatecost"}
                if dest in self.graph[key] and key!=dest:
                    if self.graph[key][dest][1] == self.src and self.router_table[dest][1] == key:
                        newTable[dest] = [float("inf"), None, 0]
                        data['info'] = newTable
                        self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
                        print(f"[{time.time()}] Message sent from Node {self.src} to Node {key}")
                        poison.append(key)

        for key in self.neighbour:
            if key not in poison:
                addr = (self.ip, key)
                data = {'type': type, 'info': table}
                self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
                print(f"[{time.time()}] Message sent from Node {self.src} to Node {key}")


def initRouter(model, src, neigh, last, change, lastneigh):
    try:
        init_time = time.time()
        router = Router(model, src, neigh, last, change, lastneigh, init_time)
        if last == 1:
            router.broadcast("updatecost",router.router_table)
        router.start()
    except KeyboardInterrupt:
        print("Exiting")

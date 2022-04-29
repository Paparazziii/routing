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
from heapq import *


class Router:
    graph = {}  # key is all other routers, value is their router table
    neighbour = []
    last = 0
    changed = 1

    def __init__(self, model, src, neigh, last, change, lastneigh, init_time, updateInterval):
        self.ip = socket.gethostbyname(socket.gethostname())
        self.src = src

        # Here is where could set ROUTING_INTERVAL
        self.routing_interval = 30

        self.update_interval = updateInterval
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
        self.pialg = {}
        self.startflag = 0
        self.afterinit = 0
        self.seq = 0
        self.graph[self.src] = {}
        self.path = {}
        # key is all routers, value is [shortest path, next-hop, isneighbour]
        for key in neigh:
            self.neighbour[int(key)] = [neigh[key], self.src, key]
            self.graph[self.src][key] = [neigh[key], self.src, key]
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
            seq = loaded["seq"]
            srcPort = loaded["srcPort"]
            ip, port = srcAddr
            newLink = {}
            changed = 0
            for key in info:
                newLink[int(key)] = info[key]
            if types == "init":
                # active the node
                self.startflag = 1
                if srcPort in self.pialg and self.pialg[srcPort] >= seq:
                    print(f"[{time.time()}] DUPLICATE LSA packet Received, AND DROPPED:")
                    print(f"- LSA of node {srcPort}")
                    print(f"- Sequence number {seq}")
                    print(f"- Received from {port}")
                    continue

                elif srcPort == self.src:
                    continue

                print(f"[{time.time()}] LSA of node {srcPort} with sequence number {seq} received from Node {port}")
                self.broadcast(types, newLink, seq, srcPort)
                self.pialg[srcPort] = seq
                self.graph[srcPort] = newLink
                self.printTop()
                initThread = Thread(target=self.startDij)
                initThread.daemon = True
                initThread.start()

            elif types == "prd":
                if srcPort in self.pialg and self.pialg[srcPort] >= seq:
                    print(f"[{time.time()}] DUPLICATE LSA packet Received, AND DROPPED:")
                    print(f"- LSA of node {srcPort}")
                    print(f"- Sequence number {seq}")
                    print(f"- Received from {port}")
                    continue

                self.broadcast(types, newLink, seq, srcPort)
                self.pialg[srcPort] = seq
                if srcPort in self.graph:
                    if self.graph[srcPort] == newLink:
                        continue
                self.graph[srcPort] = newLink
                self.printTop()
                if self.afterinit == 1:
                    initThread = Thread(target=self.regularDij())
                    initThread.start()
                    initThread.join()

    def timewaiter(self):
        while True:
            if self.startflag == 1:
                self.seq += 1
                self.broadcast("prd",self.neighbour, self.seq, self.src)
                time.sleep(self.update_interval)

    def dijkstra(self, graph, start):
        vnum = len(graph)
        paths = {}
        curr = [(0, start, start)]
        heapify(curr)
        count = 0
        nexthop = None
        minE = float('inf')
        for key in graph[start]:
            if key[0] < minE:
                minE = key[0]
                nexthop = key
        while count < vnum and curr is not None:
            plen, u, vmin = heappop(curr)
            if paths[vmin] is not None:
                continue
            paths[vmin] = [plen, nexthop]
            for nextE in graph[vmin]:
                if not paths[nextE[2]]:
                    heappush(curr, (plen + nextE[0], u, nextE[2]))
            count += 1
        return paths

    def startDij(self):
        time.sleep(self.routing_interval)
        rec = self.dijkstra(self.graph, self.src)
        self.path = rec
        self.printTop()
        self.showTable(rec)
        self.afterinit = 1

    def regularDij(self):
        origin = self.path
        rec = self.dijkstra(self.graph, self.src)
        if origin != rec:
            self.printTop()
            self.showTable(rec)

    def broadcast(self, typee, info, seq, port):
        for key in self.neighbour:
            addr = (self.ip, key)
            data = {'type': typee, 'info': info, 'seq': seq, 'srcPort': port}
            self.udpSocket.sendto(str.encode(json.dumps(data)), addr)
            print(f"[{time.time()}] LSA of Node {port} with sequence number {seq} sent to Node {key}")

    def showTable(self, path):
        print(f"[{time.time()}] Node {self.src} Routing Table")
        for i in sorted(path.keys()):
            if i != self.src:
                if path[i][1] == i:
                    print(f"- ({path[i][0]}) -> Node {i}")
                else:
                    print(f"- ({path[i][0]}) -> Node {i}; "
                          f"Next hop -> Node {path[i][1]}")

    def printTop(self):
        print(f"[{time.time()}] Node {self.src} Network Topology")
        for i in sorted(self.graph.keys()):
            for link in self.graph[i].values():
                print(f"- ({link[0]}) from Node {link[1]} to Node {link[2]}")


def initLinkState(model, src, neigh, last, change, lastneigh, updateInterval):
    try:
        init_time = time.time()
        router = Router(model, src, neigh, last, change, lastneigh, init_time, updateInterval)
        if last == 1:
            router.startflag = 1
            router.broadcast("init", router.neighbour, 0, router.src)
        router.start()
    except KeyboardInterrupt:
        print("Exiting")

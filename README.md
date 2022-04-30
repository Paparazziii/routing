# CSEE4119 Programming Assignment2

- AUTHOR: Jing Tang
- UNI: jt3300

There are three files in this project, including routenode.py(which read the arguments in and determine which mode it would get in), distanceVector.py(handle implementation for distance vector routing algorithm), and linkState.py(handle implementation for link state routing algorithm).

For Distance Vetor part, to start the program, type in:
- $ python3 routenode.py dv <r/p> <update-interval> <local-port> <neighbor1-port> <cost-1> <neighbor2-port> <cost-2> ... [last][<cost-change>]
  
  for regular nodes:
- eg. $ python3 routenode.py dv p 1 1111 2222 1 3333 50
  
  for last node:
- eg. $ python3 routenode.py dv r 1 4444 2222 8 3333 5 last
  
  for link change:
- eg. $ python3 routenode.py dv r 1 3333 1111 50 2222 10 last 5
  
(All the detailed command descriptions is followed what is given by the requirements)
  
The key point for this part the bellman-ford algorithm, and I treat it as a separate helper function so that when the graph is updated, the program would simply call this function to get a new router table.
  
The overall structure is designed as multithread. There are two startup threads, one for regular receiving, and the other one is waiting for link change. Everytime when a new message come in, after treiving the information from message, the recv thread would start a new subthread to deal with the info, so that the recv thread could continue waiting for new message and will not be blocked by bellmon-ford algorithm.
  
  
For Link State part, to start the program, type in:
- $ python3 routenode.py dv <r/p> <update-interval> <local-port> <neighbor1-port> <cost-1> <neighbor2-port> <cost-2> ... [last][<cost-change>]  
 
  for regular nodes:
- $ python3 routenode.py ls r 5 1111 2222 1 3333 50
 
  for last node:
- $ python3 routenode.py ls r 5 4444 2222 8 3333 5 last

  for link change:
- $ python3 routenode.py ls r 5 3333 1111 50 2222 2 last 60
 
(All the detailed command descriptions is followed what is given by the requirements)
  
The key point for this part is Dijkstra. After Routing_Interval, it will start the first dijkstra algorithm and get the local routing table. After that, everytime the topology is changed, it will call the Dijkstra again to get a new routing table.
  
The overall structure is also based on multi-thread. The program will start with three threads, one for receiving message, one for periodically send out LSA packets, and one for waiting for the link change.
  
After receiving the init message(which active the node), it will start a new thread to wait for the first Dijkstra algorithm after Routing Interval. When receiving regular LSA packets, it will first check if the graph need to be updated. If it does, then the program would also start a new thread to deal with the incoming info so that it will not lose any new coming messages. 
  
In order to keep the print out infomation in order and neat, I make the recv thread sleep for a very short time to wait until the print process ends by its subthread. During my testing process, it may cause some new coming packet being blocked or lost if the update_interval is very short, but because the LSA packets are sending periodically, the updating information could still reach the destination node, so it would not be a big problem. My program could still get a right routing table after all.
  
The data structure I used for neighbour is dictionary to record the neighbour with its corresponding distance. For graph, it is also a dictionary, with port number as its keyword, and its corresponding routing table(or LSA for link state) as its value. For routing table, it has destination port number, shortest path and isNeighbour as its values. For LSA, it has start point, end point, and the link between them as its values. The structure I used for these two mode is similar, so that I could easily deal with the information by similar codes.
  
All detailed test cases and their results could be found in test.txt.

import sys
import random
import threading
import time
from Queue import Queue

#Four Nodes in DataCenter. Count of Semaphore corresponds with amount of resources available in that node
num_of_nodes = 4
cpus = [[threading.Semaphore(10),10], [threading.Semaphore(5),5], [threading.Semaphore(12),12], [threading.Semaphore(2),2 ] ] 
memory = [[threading.Semaphore(15),15], [threading.Semaphore(10),10], [threading.Semaphore(20),20], [threading.Semaphore(40),40] ]

#Creating a resource offer from master side just to pass into acquire_resource_offer
def create_resource_offer(node_number):
	return [node_number, cpus[node_number][1], memory[node_number][1] ]

#Acquiring resources to use in job.
def acquire_resource_offer(list, cpus_to_grab, memory_to_grab):
	node_number = list[0]
	for x in range(cpus_to_grab):
		cpus[node_number][0].acquire()
		cpus[node_number][1] -= 1
	for x in range(memory_to_grab):
		memory[node_number][0].acquire()
		memory[node_number][1] -= 1

def job(request_q, cpus, memory):
	request_q.put([cpus, memory])

def master(request_q):
	while(1):
		job_request = request_q.get()
		print("job request: " + str(job_request))
		#Get list of available resources per node.
		resource_offers = []
		for x in range(num_of_nodes):
			resource_offers.append(create_resource_offer(x))

		#This is where we add our allocation/scheduling algorithm...
		#For now, just loop through resource_offers seeing which node can match job requirements
		for x in range(num_of_nodes):
			if resource_offers[x][1] >= job_request[0] and resource_offers[x][2] >= job_request[1]:
				print("before is: " + str(create_resource_offer(x)))
				acquire_resource_offer(resource_offers[x], job_request[0], job_request[1])
				print("after is: " + str(create_resource_offer(x)))
				break
		


#print(create_resource_offer(0))
#acquire_resource_offer(create_resource_offer(0), 2, 4)
#print(create_resource_offer(0))

request_queue = Queue()
job1 = threading.Thread(target = job, args=(request_queue, 1, 1))
job2 = threading.Thread(target = job, args=(request_queue, 2, 2))

master = threading.Thread(target = master, args = (request_queue,))

master.start()
job1.start()
job2.start()


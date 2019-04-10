import sys
import random
import threading
import time
import numpy as np
import socket
import pickle
#from Queue import Queue


#Four Nodes in DataCenter. Count of Semaphore corresponds with amount of resources available in that node
num_of_nodes = 4
cpus = [[threading.Semaphore(10),10], [threading.Semaphore(5),5], [threading.Semaphore(12),12], [threading.Semaphore(2),2 ] ] 
memory = [[threading.Semaphore(15),15], [threading.Semaphore(10),10], [threading.Semaphore(20),20], [threading.Semaphore(40),40] ]
resource_caps = [29, 85]
agent_resources = {}

def getUserDemand(userID, request_dict):
	#print(userID)
	#print(request_dict)
	if not request_dict[userID]:
		return None
	return request_dict[userID][0][0:1]

def dominantResourceFairness(resource_caps, resource_util, dominant_shares, utils, request_dict):
#do argument sort to order dom shares ascending
	sorted_dom_shares = np.argsort(dominant_shares)
	#print(sorted_dom_shares)
	#check each user to see if we can service their next request
	for i in sorted_dom_shares:
		userDemand = getUserDemand(i, request_dict)
		if not userDemand:
            #if this user doesn't have any current requests,
            #move to the next guy
			pass
        #if there is a pending request, check to see if request can be serviced
		elif np.all(userDemand + resource_util <= resource_caps):
            # ^^ all resources need to be able to accomodate the request -- if they can, proceed
            # vv simple vector addition
			resource_util += userDemand
			utils[i] += userDemand
			dominant_shares[i] = np.max(utils[i] / resource_caps)
			#print(i, resource_util, utils, dominant_shares)
			return True, resource_caps, resource_util, dominant_shares, utils, userDemand, i #return success and updated params
    #if no request can be serviced currently, return failure and the old parameters
	return False, resource_caps, resource_util, dominant_shares, utils, None, None

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

def job_func(request_dict, user, cpus, memory, jobID):
	request_dict[user].append([cpus, memory, jobID])

HOST = '10.194.31.36'
PORT = 8000

def master_func(request_dict):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	#s.setblocking(0)	
	while(1):
		#Get list of available resources per node.
		s.settimeout(1)
		try:
			data = s.recv(1024)
			if len(data) > 0:
				data = s.recv(1024)
				data = pickle.loads(data)
				#CHECK TYPE OF DATA, AGENT UPDATE OR AGENT RESOURCE OFFERS
				agent_ID = data['agent_id']
				if agent_ID in agent_resources:
						#UPDATE
					agent_resources[agent_ID]["cpu"] += data["cpu"]
					agent_resources[agent_ID]["ram"] += data["ram"]
					print("receive agent stuff")
				else:
					agent_resources[agent_ID] = data
					print("receive " + str(agent_resources))
		except Exception as e:
			pass

		resource_offers = []
		#for x in range(num_of_nodes):
		#	resource_offers.append(create_resource_offer(x))
		for k, v in agent_resources.items():
			agent_cpu = v["cpu"]
			agent_ram = v["ram"]
			resource_offers.append( [k, agent_cpu, agent_ram])

		print(resource_offers)
		numUsers = 2
		resource_utilizations = np.zeros(2)
		userUtilization = np.zeros((len(agent_resources.keys()), 2))
		userDomShares = np.zeros(len(agent_resources.keys()))
		resource_caps = [0, 0]
		for resource in resource_offers:
			resource_caps[0] += resource[1]
			resource_caps[1] += resource[2]

		#resource_caps = [29, 85]

		[success, resource_caps, resource_util, dominant_shares, utils, userDemand, i] = dominantResourceFairness(resource_caps, resource_utilizations, userDomShares, userUtilization, request_dict)

		#This is where we add our allocation/scheduling algorithm...
		#For now, just loop through resource_offers seeing which node can match job requirements
		print(success)
		if success:
			for k, v in agent_resources.items():
				if agent_resources[k]["cpu"] >= resource_util[0] and agent_resources[k]["ram"] >= resource_util[1]:
					print("send " + str(request_dict[i][0][2]))
					#ack = -1
					#while ack != request_dict[i][0][2]:
					s.send(pickle.dumps({"id": request_dict[i][0][2], "cpu": request_dict[i][0][0], "ram": request_dict[i][0][1]} ))
					agent_resources[k]["cpu"] -= resource_util[0]
					agent_resources[k]["ram"] -= resource_util[1]
					#	ack = s.recv(1024)
					#	ack = pickle.loads(ack)
					#	print(ack)
					#	ack = ack["id"]
					request_dict[i] = request_dict[i][1:]
					break
		#if success:
			#for x in range(num_of_nodes):
				#if resource_offers[x][1] >= resource_util[0] and resource_offers[x][2] >= resource_util[1]:
					#print("before is: " + str(create_resource_offer(x)))
					#acquire_resource_offer(resource_offers[x], int(resource_util[0]), int(resource_util[1]))
					#request_dict[i] = request_dict[i][1:]
					#print("job request is " + str(resource_util))
					#print("after is: " + str(create_resource_offer(x)) + "\n")
					#break
					#pass
		

def main():
	request_dict = {0:[] , 1:[], 2:[], 3:[], 4:[]}
	job1 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 1, 1))
	job2 = threading.Thread(target = job_func, args=(request_dict, 0, 2, 2, 2))
	job3 = threading.Thread(target = job_func, args=(request_dict, 0, 3, 4, 3))
	job4 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 2, 4))
	job5 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 3, 5))
	master = threading.Thread(target = master_func, args = (request_dict,))


	job1.daemon = True
	job2.daemon = True
	job3.daemon = True
	job4.daemon = True
	job5.daemon = True
	master.start()
	job1.start()
	job2.start()
	job3.start()
	job4.start()
	job5.start()

if __name__ == '__main__':
	main()
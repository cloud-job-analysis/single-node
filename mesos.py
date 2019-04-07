import sys
import random
import threading
import time
import numpy as np
from Queue import Queue

#Four Nodes in DataCenter. Count of Semaphore corresponds with amount of resources available in that node
num_of_nodes = 4
cpus = [[threading.Semaphore(10),10], [threading.Semaphore(5),5], [threading.Semaphore(12),12], [threading.Semaphore(2),2 ] ] 
memory = [[threading.Semaphore(15),15], [threading.Semaphore(10),10], [threading.Semaphore(20),20], [threading.Semaphore(40),40] ]
resource_caps = [29, 85]

def getUserDemand(userID, request_dict):
	#print(userID)
	#print(request_dict)
	if not request_dict[userID]:
		return None
	return request_dict[userID][0]

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

def job_func(request_dict, user, cpus, memory):
	request_dict[user].append([cpus, memory])


def master_func(request_dict):
	while(1):
		#job_request = request_q.get()
		#print("job request: " + str(job_request))

		#Get list of available resources per node.
		resource_offers = []
		for x in range(num_of_nodes):
			resource_offers.append(create_resource_offer(x))

		numUsers = 2
		resource_utilizations = np.zeros(2)
		userUtilization = np.zeros((numUsers, 2))
		userDomShares = np.zeros(numUsers)
		resource_caps = [29, 85]
		#print(request_dict)
		[success, resource_caps, resource_util, dominant_shares, utils, userDemand, i] = dominantResourceFairness(resource_caps, resource_utilizations, userDomShares, userUtilization, request_dict)
		#print([success, resource_caps, resource_util, dominant_shares, utils])
		#print([success, resource_caps, resource_util, dominant_shares, utils])
		#This is where we add our allocation/scheduling algorithm...
		#For now, just loop through resource_offers seeing which node can match job requirements
		print(success)
		if success:
			for x in range(num_of_nodes):
				if resource_offers[x][1] >= resource_util[0] and resource_offers[x][2] >= resource_util[1]:
					print("before is: " + str(create_resource_offer(x)))
					acquire_resource_offer(resource_offers[x], int(resource_util[0]), int(resource_util[1]))
					request_dict[i] = request_dict[i][1:]
					print("after is: " + str(create_resource_offer(x)))
					break
		

def main():
	request_dict = {0:[] , 1:[]}
	job1 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 1))
	job2 = threading.Thread(target = job_func, args=(request_dict, 1, 2, 2))
	job3 = threading.Thread(target = job_func, args=(request_dict, 0, 3, 4))

	master = threading.Thread(target = master_func, args = (request_dict,))
	#master.daemon = True
	job1.daemon = True
	job2.daemon = True
	job3.daemon = True
	master.start()
	job1.start()
	job2.start()
	job3.start()

if __name__ == '__main__':
	main()


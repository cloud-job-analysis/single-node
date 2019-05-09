import sys
import random
import threading
import time
import numpy as np
import socket
import pickle
import json
import os
import logging
#from Queue import Queue

#Framework, agent id, time it took to run job.

#Four Nodes in DataCenter. Count of Semaphore corresponds with amount of resources available in that node
num_of_nodes = 4
cpus = [[threading.Semaphore(10),10], [threading.Semaphore(5),5], [threading.Semaphore(12),12], [threading.Semaphore(2),2 ] ] 
memory = [[threading.Semaphore(15),15], [threading.Semaphore(10),10], [threading.Semaphore(20),20], [threading.Semaphore(40),40] ]
resource_caps = [29, 85]
agent_resources = {}
logging.basicConfig(filename='output.log',format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p' ,level=logging.DEBUG)

job_count = 0
total_jobs = 0
scheduling_alg = 1
job_features = {}

csv_file_name = 'output.csv'
csv_file = open(csv_file_name, 'w+')
csv_file.write('Job ID,Agent ID,RAM,CPU,Framework Type,Job Runtime\n')
csv_file.flush()
log_file_name = 'output.log'
log_file = open(log_file_name, 'w+')
throughput_file_name = 'throughput.log'
throughput_file = open(throughput_file_name, 'w+')

def getUserDemand(userID, request_dict):
	if not request_dict[userID]:
		return None
	return request_dict[userID][0][0:1]

def dominantResourceFairness(resource_caps, resource_util, dominant_shares, utils, request_dict):
#do argument sort to order dom shares ascending
	sorted_dom_shares = np.argsort(dominant_shares)
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
			return True, resource_caps, resource_util, dominant_shares, utils, userDemand, i #return success and updated params
    #if no request can be serviced currently, return failure and the old parameters
	return False, resource_caps, resource_util, dominant_shares, utils, None, None

def shortestJobFirst(resource_caps, request_dict):
    request_over = list(request_dict.values())
    request_list = request_over[0]
    #sort jobs according to reported predicted job time (ascending)
    sorted_requests = sorted(request_list, key=lambda x: x[5])
    #loop through all (sorted) requests
    for request in sorted_requests:
        #for this request, if all of it's resource constraints (omit job time)
        #can be serviced, then run this job
        if np.all(request[0:2] <= resource_caps):
            return True, request
        
    #if no request can be serviced, return failure and None for the request we're servicing
    return False, None

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

#Adding in job requests inside the request dictionary
def job_func(request_dict, user, cpus, memory, jobID, command, type, predicted):
	request_dict[user].append([cpus, memory, jobID, command, type, predicted, user])

HOST = '0.0.0.0'
PORT = 8000

def master_func(request_dict):

	#initializing variables for mesos master
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	global job_count
	global total_jobs
	resource_utilizations = np.zeros(2)
	userUtilization = np.zeros((5, 2))
	userDomShares = np.zeros((5))
	start = time.time()

	#Start Mesos Master
	while(1):
		#Get list of available resources per node.
		s.settimeout(8)
		try:
			data = s.recv(1024)
			if len(data) > 0:
				data = pickle.loads(data)
				print(data)
				#CHECK TYPE OF DATA, AGENT UPDATE OR AGENT RESOURCE OFFERS
				agent_ID = data['agent_id']
				if agent_ID in agent_resources:
					#Updating resource offers after an agent has completed a job
					agent_resources[agent_ID]["cpu"] += data["cpu"]
					agent_resources[agent_ID]["ram"] += data["ram"]
					job_count -= 1
					#Write to csv
					csv_str = str(data['id']) + ',' + str(data['agent_id']) + ',' + str(data['ram']) + ',' + \
					str(data['cpu']) + ',' + str(data['type']) + ',' + str(data['job_runtime']) + "," + str(job_features[data['id']])
					csv_file.write(csv_str+'\n')
					csv_file.flush()
					#print remaining jobs to run and escaping if they have reached 0
					print("JOB COUNT IS " + str(job_count))
					resource_utilizations[0] -= data['cpu']
					resource_utilizations[1] -= data['ram']
					userUtilization[data['user_id']][0] -= data['cpu']
					userUtilization[data['user_id']][1] -= data['ram']
					userDomShares[data['user_id']] = np.max(userUtilization[data['user_id']] / resource_caps)
					if job_count == 0:
						break
				else:
					#Adding in a new resource offer for a new agent
					agent_resources[agent_ID] = data
					print("receive " + str(agent_resources))
		except socket.timeout as e:
			print (e)
			pass

		#Adding in resource offers to a cleaner format
		resource_offers = []
		for k, v in agent_resources.items():
			agent_cpu = v["cpu"]
			agent_ram = v["ram"]
			resource_offers.append( [k, agent_cpu, agent_ram])

		#Determining resource caps
		resource_caps = [0, 0]
		for resource in resource_offers:
			resource_caps[0] += resource[1]
			resource_caps[1] += resource[2]

		#DRF Scheduling Algorithm
		if scheduling_alg == 0:
			[success, resource_caps, resource_util, dominant_shares, utils, userDemand, i] = dominantResourceFairness(resource_caps, resource_utilizations, userDomShares, userUtilization, request_dict)
			resource_utilizations = resource_util
			userUtilization = utils
			userDomShares = dominant_shares
			job_i = 0
		#SJF Scheduling Algorithm
		elif scheduling_alg == 1:
			[success, request] = shortestJobFirst(resource_caps, request_dict)
			val = list(request_dict.values())
			i = 0
			for value in val:
				idx = 0
				for v in value:
					if v == request:
						job_i = idx
					idx += 1

		#Sending scheduled job to agent
		print(success)
		if success:
			for k, v in agent_resources.items():
				if agent_resources[k]["cpu"] >= request_dict[i][job_i][0] and agent_resources[k]["ram"] >= request_dict[i][job_i][1]:
					print("send job # " + str(request_dict[i][job_i][2]) + " cpu " + str(request_dict[i][job_i][0]) + " ram " + str(request_dict[i][job_i][1]))
					#Decrementing resources that job is using
					agent_resources[k]["cpu"] -= request_dict[i][job_i][0]
					agent_resources[k]["ram"] -= request_dict[i][job_i][1]
					s.send(pickle.dumps({"id": request_dict[i][job_i][2], "cpu": request_dict[i][job_i][0], "ram": request_dict[i][job_i][1], "command": request_dict[i][job_i][3], "type": request_dict[i][job_i][4], "user_id": i  }))
					#Get rid of job request from request dict
					request_dict[i] = request_dict[i][0:job_i] + request_dict[i][job_i+1:]
					break
		if job_count == 0:
			break
	#Write throuhgput after master has finished running all jobs
	total_run_time = time.time() - start
	throughput = total_jobs/total_run_time
	th_str = str(throughput)
	throughput_file.write(th_str)
	throughput_file.flush()	

def main():
	request_dict = {0:[]}
	if scheduling_alg == 0:
		request_dict[1] = []
		request_dict[2] = []
		request_dict[3] = []
		request_dict[4] = []

	global job_count
	global total_jobs
	global job_features 
	f = open("data_final.json", "r")
	data = f.read()
	data = data.split("\n")[:-1]
	#counting number of jobs
	for job in data:
		job_count += 1
		total_jobs += 1
		job = json.loads(job)
		job_features[job["id"]] = job["feature"]

	#Adding jobs into request dict
	for job in data:	
		job = json.loads(job)
		r1 = random.randint(0,4)
		if scheduling_alg == 0:
			threading.Thread(target = job_func, args=(request_dict, r1, job["cpu"], job["ram"], job["id"], job["command"], job["type"], job["predicted"]), daemon=True).start()
		else:
			threading.Thread(target = job_func, args=(request_dict, 0, job["cpu"], job["ram"], job["id"], job["command"], job["type"], job["predicted"]), daemon=True).start()

	threading.Thread(target = master_func, args = (request_dict,)).start()
if __name__ == '__main__':
	main()

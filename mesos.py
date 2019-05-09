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
scheduling_alg = 0
job_features = {}

csv_file_name = 'output.csv'
csv_file = open(csv_file_name, 'w+')
csv_file.write('Job ID,Agent ID,RAM,CPU,Framework Type,Job Runtime\n')
csv_file.flush()
log_file_name = 'output.log'
log_file = open(log_file_name, 'w+')
throughput_file_name = 'throughput.log'
throughput_file = open(throughput_file_name, 'w+')
agent_id_map = {}


user_job_dict = {}

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

def shortestJobFirst(resource_caps, request_dict):
    request_over = list(request_dict.values())
    request_list = request_over[0]
    #sort jobs according to reported predicted job time (ascending)
    sorted_requests = sorted(request_list, key=lambda x: x[5]) ########################
    ############Need to change this to reflect that we're sorting according to reported predicted job time
    print(sorted_requests)
    #loop through all (sorted) requests
    for request in sorted_requests:
        #for this request, if all of it's resource constraints (omit job time)
        #can be serviced, then run this job
        print("REQUEST IN SJF IS ")
        print(request)
        if np.all(request[0:2] <= resource_caps):
            #if np.all(request[:-1] <= resource_caps):
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

def job_func(request_dict, user, cpus, memory, jobID, command, type, predicted):
	request_dict[user].append([cpus, memory, jobID, command, type, predicted])

HOST = '0.0.0.0'
PORT = 8000
PORT_2 = 8001

def master_func(request_dict):
	global agent_id_map
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s2.connect((HOST, PORT_2))
	resource_utilizations = np.zeros(2)
	userUtilization = np.zeros((5, 2))
	userDomShares = np.zeros((5))
	global job_count
	global total_jobs
	start = time.time()
	#s.setblocking(0)
	while(1):
		#Get list of available resources per node.
		s.settimeout(8)
		try:
			data = s.recv(1024)
			#print (len(data))
			#print(data)
			#print (pickle.loads(data))
			if len(data) > 0:
				# data = s.recv(1024)
				data = pickle.loads(data)
				#CHECK TYPE OF DATA, AGENT UPDATE OR AGENT RESOURCE OFFERS
				agent_ID = data['agent_id']
				if agent_ID in agent_resources:
						#UPDATE
					agent_resources[agent_ID]["cpu"] += data["cpu"]
					agent_resources[agent_ID]["ram"] += data["ram"]
					#print("receive agent stuff %d ", data["job_runtime"])
					print("DATA IS RECEIVED %d %d %f" % (data['id'], data['agent_id'], data['job_runtime']))
					log_str = "agent id: " + str(data['agent_id']) + " Job Runtime: " + str(data['job_runtime']) + " Framework Type: " \
					+ str(data["type"]) + " cpu: " + str(data["cpu"]) + " ram: " + str(data["ram"])  
					#logging.DEBUG(log_str)
					job_count -= 1
					log_file.write(log_str + "\n")
					log_file.flush()
					#print("BEFORE CSV WORKING")
					csv_str = str(data['id']) + ',' + str(data['agent_id']) + ',' + str(data['ram']) + ',' + \
					str(data['cpu']) + ',' + str(data['type']) + ',' + str(data['job_runtime']) + "," + str(job_features[data['id']])
					#print("AFTER CSV WORKING")
					csv_file.write(csv_str+'\n')
					csv_file.flush()
					#print("AFTER CSV WROTE")
					job_id = data['id']
					user_id = user_job_dict[job_id]
					print("JOB COUNT IS " + str(job_count))
					resource_utilizations[0] -= data['cpu']
					resource_utilizations[1] -= data['ram']
					userUtilization[user_id][0] -= data['cpu']
					userUtilization[user_id][1] -= data['ram']
					userDomShares[user_id] = np.max(userUtilization[user_id] / resource_caps)
					print("JOB COUNT IS " + str(job_count))
					if job_count == 0:
						break
				else:
					agent_resources[agent_ID] = data
					if len(agent_id_map.keys()) == 0 :
						agent_id_map[agent_ID] = 0
					else:
						a = list(agent_id_map.values())
						next_k = max(a)
						agent_id_map[agent_ID] = next_k + 1
					#print("receive " + str(agent_resources))
		except socket.timeout as e:
			print (e)
			pass
		
		s2.settimeout(8)
		try:
			data = s2.recv(1024)
			#print (len(data))
			#print(data)
			#print (pickle.loads(data))
			if len(data) > 0:
				# data = s.recv(1024)
				data = pickle.loads(data)
				#CHECK TYPE OF DATA, AGENT UPDATE OR AGENT RESOURCE OFFERS
				agent_ID = data['agent_id']
				if agent_ID in agent_resources:
						#UPDATE
					agent_resources[agent_ID]["cpu"] += data["cpu"]
					agent_resources[agent_ID]["ram"] += data["ram"]
					#print("receive agent stuff %d ", data["job_runtime"])
					print("DATA IS RECEIVED %d %d %f" % (data['id'], data['agent_id'], data['job_runtime']))
					log_str = "agent id: " + str(data['agent_id']) + " Job Runtime: " + str(data['job_runtime']) + " Framework Type: " \
					+ str(data["type"]) + " cpu: " + str(data["cpu"]) + " ram: " + str(data["ram"])  
					#logging.DEBUG(log_str)
					job_count -= 1
					log_file.write(log_str + "\n")
					log_file.flush()
					#print("BEFORE CSV WORKING")
					csv_str = str(data['id']) + ',' + str(data['agent_id']) + ',' + str(data['ram']) + ',' + \
					str(data['cpu']) + ',' + str(data['type']) + ',' + str(data['job_runtime']) + "," + str(job_features[data['id']])
					#print("AFTER CSV WORKING")
					csv_file.write(csv_str+'\n')
					csv_file.flush()
					#print("AFTER CSV WROTE")
					job_id = data['id']
					user_id = user_job_dict[job_id]
					print("JOB COUNT IS " + str(job_count))
					resource_utilizations[0] -= data['cpu']
					resource_utilizations[1] -= data['ram']
					userUtilization[user_id][0] -= data['cpu']
					userUtilization[user_id][1] -= data['ram']
					userDomShares[user_id] = np.max(userUtilization[user_id] / resource_caps)
					print("JOB COUNT IS " + str(job_count))
					if job_count == 0:
						break
				else:
					agent_resources[agent_ID] = data
					if len(agent_id_map.keys()) == 0 :
						agent_id_map[agent_ID] = 0
					else:
						a = list(agent_id_map.values())
						next_k = max(a)
						agent_id_map[agent_ID] = next_k + 1
					#print("receive " + str(agent_resources))
		except socket.timeout as e:
			print (e)
			pass

		resource_offers = []
		#for x in range(num_of_nodes):
		#	resource_offers.append(create_resource_offer(x))
		for k, v in agent_resources.items():
			agent_cpu = v["cpu"]
			agent_ram = v["ram"]
			resource_offers.append( [k, agent_cpu, agent_ram])

		print(resource_offers)
		resource_caps = [0, 0]
		for resource in resource_offers:
			resource_caps[0] += resource[1]
			resource_caps[1] += resource[2]

		#resource_caps = [29, 85]
		if scheduling_alg == 0:
			[success, resource_caps, resource_util, dominant_shares, utils, userDemand, i] = dominantResourceFairness(resource_caps, resource_utilizations, userDomShares, userUtilization, request_dict)
			job_i = 0
			resource_utilizations = resource_util
			userUtilization = utils
			userDomShares = dominant_shares
		elif scheduling_alg == 1:
			[success, request] = shortestJobFirst(resource_caps, request_dict)
			val = list(request_dict.values())
			#print("THE REQUEST AFTER SJF IS ")
			#print(request)
			i = 0
			for value in val:
				idx = 0
				for v in value:
					if v == request:
						job_i = idx
					idx += 1


		#This is where we add our allocation/scheduling algorithm...
		#For now, just loop through resource_offers seeing which node can match job requirements
		print(success)
		if success:
			for k, v in agent_resources.items():
				if agent_resources[k]["cpu"] >= request_dict[i][job_i][0] and agent_resources[k]["ram"] >= request_dict[i][job_i][1]:
					print("send " + str(request_dict[i][job_i][2]) + " cpu " + str(request_dict[i][job_i][0]) + " ram " + str(request_dict[i][job_i][1]) + " agent id is: " + str(k))
					#ack = -1
					#while ack != request_dict[i][0][2]:
					# Remove
					#print("cpu resource util is " + str(resource_util[0]) + " ram resource util is " + str(resource_util[1]))
					#s.send(pickle.dumps({"id": request_dict[i][0][2], "cpu": request_dict[i][0][0], "ram": request_dict[i][0][1], "command": request_dict[i][0][3], "type": request_dict[i][0][4]}))
					# Remove
					#else:
					print(k)
					print(agent_id_map)
					agent_resources[k]["cpu"] -= request_dict[i][job_i][0]
					agent_resources[k]["ram"] -= request_dict[i][job_i][1]
					user_job_dict[request_dict[i][job_i][2]] = i
					if agent_id_map[k] == 0:
						s.send(pickle.dumps({"id": request_dict[i][job_i][2], "cpu": request_dict[i][job_i][0], "ram": request_dict[i][job_i][1], "command": request_dict[i][job_i][3], "type": request_dict[i][job_i][4]}))
					elif agent_id_map[k] == 1:
						s2.send(pickle.dumps({"id": request_dict[i][job_i][2], "cpu": request_dict[i][job_i][0], "ram": request_dict[i][job_i][1], "command": request_dict[i][job_i][3], "type": request_dict[i][job_i][4]}))
					#	ack = s.recv(1024)
					#	ack = pickle.loads(ack)
					#	print(ack)
					#	ack = ack["id"]
					request_dict[i] = request_dict[i][0:job_i] + request_dict[i][job_i+1:]
					break
		if job_count == 0:
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
	#job1 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 1, 1))
	#job2 = threading.Thread(target = job_func, args=(request_dict, 0, 2, 2, 2))
	#job3 = threading.Thread(target = job_func, args=(request_dict, 0, 3, 4, 3))
	#job4 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 2, 4))
	#job5 = threading.Thread(target = job_func, args=(request_dict, 0, 1, 3, 5))
	threading.Thread(target = master_func, args = (request_dict,)).start()


	# job1.daemon = True
	# job2.daemon = True
	# job3.daemon = True
	# job4.daemon = True
	# job5.daemon = True
	# master.start()
	# job1.start()
	# job2.start()
	# job3.start()
	# job4.start()
	# job5.start()
	global job_count
	global total_jobs
	global job_features 
	f = open("data.json", "r")
	data = f.read()
	data = data.split("\n")[:-1]
	for job in data:
		job_count += 1
		total_jobs += 1
		job = json.loads(job)
		job_features[job["id"]] = job["feature"]

	for job in data:	
		job = json.loads(job)
		r1 = random.randint(0,4)
		if scheduling_alg == 0:
			threading.Thread(target = job_func, args=(request_dict, r1, job["cpu"], job["ram"], job["id"], job["command"], job["type"], job["predicted"]), daemon=True).start()
		else:
			threading.Thread(target = job_func, args=(request_dict, 0, job["cpu"], job["ram"], job["id"], job["command"], job["type"], job["predicted"]), daemon=True).start()

if __name__ == '__main__':
	main()

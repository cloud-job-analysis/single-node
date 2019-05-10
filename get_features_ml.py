import json
import pickle
import random
import numpy as np

f = open("test_jobs.json", "r")
data = f.read()
f.close()
data = data.split("\n")[:-1]
file_size = [4, 1600, 1600, 1600, 1600]
sort = ['tim', 'bogo', 'insertion', 'bubble', 'word_count']
dataset = {"wine": [178, 13, 3], "mnist": [1797, 64, 10], "cancer": [569, 30, 2], "iris": [150, 4, 3]}
file_sizes = {}
with open('./MapReduce/folder_sizes.pkl', 'rb') as f:
	file_sizes = pickle.load(f)
features = list()
f = open('test_jobs_final.json', 'w')
with open('ML_predictor.pkl', 'rb') as ml_predictor:
	clf_ml = pickle.load(ml_predictor)

with open('MR_predictor.pkl', 'rb') as mr_predictor:
	clf_mr = pickle.load(mr_predictor)

with open('flask_predictor.pkl', 'rb') as flask_predictor:
	clf_flask = pickle.load(flask_predictor)

for job in data:
	#print(job)
	job = json.loads(job)
	predicted = -1
	if job["type"] == "flask_job":
		command = job["command"]
		command = command.split("/")[-1].split('.')[0].split('test')[1]
		feature = ["flask_job", file_size[int(command[0]) - 1], sort[int(command[1]) - 1]]
		prediction_feature = [float(feature[1])] +  [0 for i in range(5)]
		#print(prediction_feature)
		if feature[2] == 'word_count':
			prediction_feature[1] = 1
		elif feature[2] == 'tim':
			prediction_feature[2] = 1
		elif feature[2] == 'insertion':
			prediction_feature[3] = 1
		elif feature[2] == 'bubble':
			prediction_feature[4] = 1
		elif feature[2] == 'bogo':
			prediction_feature[5] = 1
		else:
			print('SOMETHING BROKEEEEE')
		#print(prediction_feature)
		predicted = clf_flask.predict(np.array(prediction_feature).reshape(1,-1))[0]
	elif job["type"] == "ml":
		command = job["command"]
		command = command.split(" ")[-1]
		feature = ["ml"] + dataset[command]
		prediction_feature = feature[1:]
		predicted = clf_ml.predict(np.array(prediction_feature).reshape(1,-1))[0]
		#print(predicted)
	elif job["type"] == "mr_job":
		command = job["command"]
		command = command.split(" ")
		prev = ''
		feature = []
		mappers = -1
		reducers = -1
		input_size = -1
		for element in command:
			if prev == '-D':
				number = int(element.split('=')[-1])
				if 'map.tasks' in element:
					mappers = number
				else:
					reducers = number
			elif prev == '-input':
				dir_name = '/' + element.split('/')[-1]
				input_size = file_sizes[dir_name]
			prev = element
		feature = ["mr_job", input_size, mappers, reducers]
		prediction_feature = feature[1:]
		predicted = clf_mr.predict(np.array(prediction_feature).reshape(1,-1))[0]
		#print(predicted)
	job["feature"] = feature
	job["predicted"] = predicted
	f.write(json.dumps(job) + '\n')
f.close()
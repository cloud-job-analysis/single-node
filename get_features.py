import json
f = open("data.json", "r")
data = f.read()
f.close()
data = data.split("\n")[:-1]
file_size = [4, 1600, 1600, 1600, 1600]
sort = ['tim', 'bogo', 'insertion', 'bubble', 'word_count']
dataset = {"wine": [178, 13, 3], "mnist": [1797, 64, 10], "cancer": [569, 30, 2], "iris": [150, 4, 3]}
features = list()
f = open('data_final.json', 'w')
for job in data:
	#print(job)
	job = json.loads(job)
	if job["type"] == "flask_job":
		command = job["command"]
		command = command.split("/")[-1].split('.')[0].split('test')[1]
		feature = ["flask_job", file_size[int(command[0]) - 1], sort[int(command[1]) - 1]]
	elif job["type"] == "ml":
		command = job["command"]
		command = command.split(" ")[-1]
		feature = ["ml"] + dataset[command]
	elif job["type"] == "mr_job":
		command = job["command"]
		command = command.split(" ")
		prev = ''
		feature = []
		mappers = -1
		reducers = -1
		for element in command:
			if prev == '-D':
				number = int(element.split('=')[-1])
				if 'map.tasks' in element:
					mappers = number
				else:
					reducers = number
			prev = element
	job["feature"] = feature
	f.write(json.dumps(job) + '\n')
f.close()
import numpy as np

f =open('flask-jobs.json', 'w+')
start_id = 3000

for i in range(500):
    ram = str(np.random.randint(1, 5))
    cpu = str(np.random.randint(1, 4))
    fname = ['test12', 'test11', 'test13', 'test14', 'test15', 'test21', 'test23', 'test24', 'test25', 'test31', 'test33', 'test34', 'test35', 'test41', 'test43', 'test44', 'test45', 'test51', 'test53', 'test54', 'test55']
    fp = fname[np.random.randint(0, len(fname))]
    json_str = "{\"ram\": " + ram + ", \"id\": " + str(start_id) + ", \"type\": \"flask_job\", \"command\": \"python flask/" + fp + ".py\", \"cpu\": " + cpu + "}"
    f.write(json_str+"\n")
    start_id += 1
f.close()
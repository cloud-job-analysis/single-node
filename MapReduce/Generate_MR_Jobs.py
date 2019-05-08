
# coding: utf-8

# In[5]:


import numpy as np


# In[6]:


files = ["/in" + str(i+1) for i in range(30)]


# In[15]:


with open('MR_Jobs.txt', 'w') as f:
    for i in range(100):
        job_name = "/usr/local/hadoop/bin/hadoop jar /usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.1.2.jar"
        job_name += " -D mapred.map.tasks="
        job_name += str(np.random.randint(1, 11))
        job_name += " -D mapred.reduce.tasks="
        job_name += str(np.random.randint(1,5))
        job_name += " -mapper MapReduce/mapper.py -reducer MapReduce/reducer.py -input "
        job_name += files[np.random.randint(0, 30)]
        job_name += " -output /" + str(i) + "\n"
        f.write(job_name)


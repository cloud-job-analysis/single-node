# Mesos Master/Single Node Notes
Mesos Master Node communicates with frameworks + agents (client nodes). 
The master enables fine-grained sharing of resources (CPU, RAM, …) across frameworks by making them resource offers. Each resource offer contains a list of <agent ID, resource1: amount1, resource2: amount2, ...>   
Master Determines how many resources to offer to each framework.

![alt text](http://mesos.apache.org/assets/img/documentation/architecture-example.jpg)

In here:   
1.) The agents will inform the mesos master of the resources it contains.  
2.) The Mesos Master will send a resource offer to framework 1.  
3.) Framework will decide which resources to utilize using tasks  
4.) Master sends tasks to agents  

Since we are working with individual jobs instead of frameworks, steps 2 + 3 become unnecessary.  
Instead, the Mesos Master itself should act as the framework scheduler for the individual jobs, denying resource offers that aren’t relevant.   
In order to satisfy the constraints of a framework, the framework themselves would usually have the ability to deny resource offers. Instead, we’d have to have the master node take on this task.  
Allocation Policy Module -> which jobs (previously frameworks) should be given what resource offers?  
Right now, Mesos just uses a module plugin, two exist right now. A fair sharing module + strict priority.  
This would be where we add in our code for scheduling algorithm (DRF, etc..)  
Job (Previously Framework) scheduler -> which resource offers fit the job’s contraints?   
Not sure on how to model this at this point, master would have to decide, is this even something we should model? Should we just say that if a resource offer exists that matches the resources needed for a job we just allocate?  

#### Instructions

1. Install numpy `pip install numpy`

2. Make sure you have python3 installed

3. Clone this repository

4. `cd single-node`

5. Open mesos.py

6. Set HOST = IP Address of the machine which is running the Agent

   Note: In case you're running the master and agent on the same machine, don't change the value of host. Let it be equal to 0.0.0.0

7. Once the agent is up, run python3 mesos.py 
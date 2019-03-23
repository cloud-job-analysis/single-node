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

## Assumptions when coding:   
Jobs are threads  
Resources are modeled using semaphores  
How long a resource needs to be grabbed should be from the job perspective, not master.  

## Other Design  
Have a master thread and multiple slave (job) threads. Communicate using message passing (like RPC) or with queues.   
Connect job threads to master thread-> have each job thread’s requests enter a waiting queue.  
Infinite while loop for master thread. Constantly accepting new job threads.   
When master thread allocation/scheduling algorithm is done, contact job thread, have job thread access   

Need a better way to keep track of which jobs hold which resources in which nodes.

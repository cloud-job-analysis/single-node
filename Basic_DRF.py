
# coding: utf-8

# In[3]:


import numpy as np


# In[1]:


def dominantResourceFairness(resource_caps, resource_util, dominant_shares, utils):
    #do argument sort to order dom shares ascending
    sorted_dom_shared = np.argsort(dominant_shares)
    #check each user to see if we can service their next request
    for i in sorted_dom_shares:
        userDemand = getUserDemand(i)
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
            return True, resource_caps, resource_util, dominant_shares, utils #return success and updated params
    #if no request can be serviced currently, return failure and the old parameters
    return False, resource_caps, resource_util, dominant_shares, utils


# In[5]:


numUsers = 10
resources = np.array([1, 2, 3, 4, 5])
resource_utilizations = np.zeros(5)
userUtilization = np.zeros((numUsers, resources.shape[0]))
userDomShares = np.zeros(numUsers)


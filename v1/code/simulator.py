
import math
import random
import numpy as np
import matplotlib.pyplot as plt
import datetime

def main():
	#HW2 2.1
	findWarmupPeriod(arrivalRate=1/2,
					 serviceRate=1/1,
					 queueLength=5,
					 numServers=2,
					 numCustomersAtStart=0,
					 simulationTime=100,
					 numSimulations=1000)


	#HW2 2.2
	findWarmupPeriod(arrivalRate=1/2,
					 serviceRate=1/1,
					 queueLength=5,
					 numServers=2,
					 numCustomersAtStart=7,
					 simulationTime=100,
					 numSimulations=1000)


	#HW2 2.3
	findWarmupPeriod(arrivalRate=1/10,
					 serviceRate=1/1,
					 queueLength=5,
					 numServers=2,
					 numCustomersAtStart=0,
					 simulationTime=100,
					 numSimulations=1000)


	#HW2 2.4
	findWarmupPeriod(arrivalRate=1/10,
					 serviceRate=1/1,
					 queueLength=5,
					 numServers=2,
					 numCustomersAtStart=4,
					 simulationTime=100,
					 numSimulations=1000)


	#HW2 3 for System A
	#Metrics for System A
	findMetrics(arrivalRate=1/2,
				serviceRate=1/1,
				queueLength=5,
				numServers=2,
				warmupPeriod=20,
				batchSize=1000,
				maxCustomersPerBatch=2000)


	#HW2 3 for System B
	#Metrics for System B
	findMetrics(arrivalRate=1/10,
				serviceRate=1/1,
				queueLength=5,
				numServers=2,
				warmupPeriod=10,
				batchSize=1000,
				maxCustomersPerBatch=10000)


#Simulate and Plot the graphical representation to enable the user to identify the Stationary State
def findWarmupPeriod(arrivalRate, serviceRate, queueLength, numServers, numCustomersAtStart, simulationTime, numSimulations):
    numCustomersList = []
    n=0
    while(n<numSimulations):
        random.seed(n)
        #Initialize the Controller
        controller = Controller(arrivalRate, serviceRate, queueLength, numServers)
        if numCustomersAtStart == 0:
            controller.init()
        else:
            controller.initNonEmptyState(numCustomersAtStart)
        
        #Continue till threshold reached
        while(controller.warmupStoppingCondition(simulationTime)):
            controller.processEvent()
            
        #Collect and store the mean number of customers in the system
        numCustomers = controller.getCustomersAtEveryDeltaT(1)
        numCustomersList.append(numCustomers[0:simulationTime])
        n=n+1
    
    #Average on all the simulations and Plot the result
    numCustomersArr = np.array(numCustomersList)
    numCustomersFinal = np.mean(numCustomersArr,axis=0) 
    plt.plot(range(0,simulationTime),numCustomersFinal[0:simulationTime])
    plt.ylim([0,queueLength+numServers])
    plt.show()    


#Simulate and Capture the Key metrics for the given queueing system
def findMetrics(arrivalRate, serviceRate, queueLength, numServers, warmupPeriod, batchSize, maxCustomersPerBatch):
    #Initialize the Controller
    controller = Controller(arrivalRate, serviceRate, queueLength, numServers)
    controller.init()
    
    #Setup batch initialization
    controller.warmupPeriod = warmupPeriod
    controller.batchSize = batchSize
    controller.maxCustomersPerBatch = maxCustomersPerBatch
    
    #For each batch, compute the required metrics
    while(controller.batchStoppingCondition()):
        controller.processBatchEvent()
    
    #Aggregate the metrics for all the batches
    meanCustArr = np.array(controller.meanCustomers)
    meanCustmean = np.mean(meanCustArr)
    meanCustSD = np.std(meanCustArr,ddof=1)
    err = 1.645 * math.sqrt(meanCustSD*meanCustSD/len(meanCustArr)) #confidence interval @90%
    print("Mean Customers in the System:" + str(round(meanCustmean,4)) + ", err:" + str(round(err,4)))

    
    bpArr = np.array(controller.blockingProbability)
    bpMean = np.mean(bpArr)
    bpSD = np.std(bpArr,ddof=1)
    err = 1.645 * math.sqrt(bpSD*bpSD/len(bpArr)) #confidence interval @90%
    print("Blocking Probability:" + str(round(bpMean,4)) + ", err:" + str(round(err,4)))
    
    meanRTArr = np.array(controller.meanResponseTime)
    meanRTmean = np.mean(meanRTArr)
    meanRTSD = np.std(meanRTArr,ddof=1)
    err = 1.645 * math.sqrt(meanRTSD*meanRTSD/len(meanRTArr)) #confidence interval @90%
    print("Mean Time Customer Spends in the System:" + str(round(meanRTmean,4)) + ", err:" + str(round(err,4)))

    return meanCustArr, bpArr, meanRTArr


#Class to generate Next arrival and Service Times
class RandomVariates:
    
    def __init__(self, _arrivalRate, _serviceRate):
        self.arrivalRate = _arrivalRate
        self.serviceRate = _serviceRate

    def expVariate(self,rate):
        return -math.log(1.0 - random.random()) *  rate
    
    def getNextArrival(self):
        return self.expVariate(self.arrivalRate)
        
    def computeServiceTime(self):
        return self.expVariate(self.serviceRate)



#Event class which has attributes defining the event i.e eventType, eventTime, customerID
class Event:
    
    def __init__(self, _eventType, _eventTime, _customerID):
        self.eventType = _eventType
        self.eventTime = _eventTime
        self.customerID = _customerID
        
#Linked List to store the events in the system
class EventList:
    
    def __init__(self):
        self.Events = []
    
    #Insert Event based on the time
    def insertNewEvent(self,_eventType, _eventTime, _customerID):
        event = Event(_eventType, _eventTime, _customerID)
        i = len(self.Events)
        while(i > 0 and event.eventTime < self.Events[i-1].eventTime): 
            i=i-1
        self.Events.insert(i,event)
    
    #Get the next event based on the given time
    def getNextEvent(self, time):
        i = len(self.Events)
        while(i>0 and self.Events[i-1].eventTime > time):
            i=i-1
        return self.Events[i]
    
    #Remove the given events
    def removeEvents(self,_events):
        for event in _events:
            self.Events.remove(event)
    
    #Get all the events for a particular customer ID
    def getEvents(self,_customerID):
        i = len(self.Events)
        events = [self.Events[i] for i in range(len(self.Events)) if self.Events[i].customerID == _customerID]
        return events    


#Data structure to store the required data to compute the mean numbers of customers in the system
class CustomersState:
    
    def __init__(self, _numCustomers, _time):
        self.numCustomers = _numCustomers
        self.time = _time


#Master Class
class Controller:
            
    def __init__(self,_arrivalRate, _serviceRate, _queueLength, _numServers):
        self.EventList = EventList()
        self.rv = RandomVariates(_arrivalRate, _serviceRate)
        self.warmupPeriod = 0
        
        #Server State
        self.numServers  = _numServers
        self.busyServers = 0
        
        #Queue State
        self.queueLength = _queueLength
        self.queue = []
        
        #System State
        self.customersState = []
        self.responseTime = []
        self.totalCustomers = 0
        self.blockedCustomers = 0
        self.clock=0
        
        #MBatch Parameters
        self.stationaryState = False
        self.batchIndex = 0
        self.batchSize = 0
        self.warmupPeriod = 0
        self.maxCustomersPerBatch = 0
        
        #Metrics collected for each batch run
        self.meanCustomers = []
        self.blockingProbability = []
        self.meanResponseTime = []
        
    #Initialization routine when the system starts with zero customers
    def init(self):
        #Get the Next Arrival
        self.EventList.insertNewEvent('Arrival', self.rv.getNextArrival(), 1)
        #Capture number of customers in the system
        self.customersState.append(CustomersState(len(self.queue)+self.busyServers,self.clock))
        
    #Initialization routine when the systems starts with non empty state
    def initNonEmptyState(self,_numCustomers):
        #Set Server Status
        self.busyServers = self.numServers if _numCustomers - self.numServers >=0 else _numCustomers

        #Set Queue Status
        for i in range(self.numServers+1, _numCustomers+1):
            self.queue.insert(0,i)

        #Get the Next Arrival
        self.EventList.insertNewEvent('Arrival', self.rv.computeServiceTime(), _numCustomers+1)
        
        #Get the Departures for customers in process
        for i in range(1, self.numServers+1):
            self.EventList.insertNewEvent('Departure', self.rv.computeServiceTime(), i)
            
        #Capture number of customers in the system
        self.customersState.append(CustomersState(len(self.queue)+self.busyServers,self.clock))
        
    #Routine to investigate the warm-up period
    def processEvent(self):    
         
        #Timing Routine
        event = self.EventList.getNextEvent(self.clock)
        self.clock = event.eventTime
        
        #Event Routine
        if event.eventType=='Arrival':
            self.EventArrival(event.customerID)
        elif event.eventType=='Departure':
            self.EventDeparture(event.customerID)
   
        self.customersState.append(CustomersState(len(self.queue)+self.busyServers,self.clock))
            
    #Routine to capture metrics during the stationary State
    def processBatchEvent(self):    
        
        #Timing Routine
        event = self.EventList.getNextEvent(self.clock)
        self.clock = event.eventTime
        
        #Event Routine
        if event.eventType=='Arrival':
            self.EventArrival(event.customerID)
        elif event.eventType=='Departure':
            self.EventDeparture(event.customerID)
   
        #Start of Stationary Period
        if(self.stationaryState==False and self.clock > self.warmupPeriod):
            self.stationaryState=True
            self.batchIndex = 1
            self.resetSystemState()

        #After completion of each batch, Update statistics and reset counters.
        if (self.stationaryState==True and self.totalCustomers > self.maxCustomersPerBatch):
            self.captureSystemState()
            self.resetSystemState()
            self.batchIndex = self.batchIndex+1
            
        self.customersState.append(CustomersState(len(self.queue)+self.busyServers,self.clock))
  
    #Reset at the end of each batch
    def resetSystemState(self):
        self.customersState = []
        self.totalCustomers = 0
        self.blockedCustomers = 0
        self.responseTime=[]
        
    #Capture system state at the end of each batch
    def captureSystemState(self):
        #Mean number of customers in the system
        meanCustomers = self.getMeanCustomers()
        self.meanCustomers.append(meanCustomers)
        self.blockingProbability.append(self.blockedCustomers/self.totalCustomers)
        self.meanResponseTime.append(np.mean(np.array(self.responseTime)))
        
    #Routine to handle Event arrival
    def EventArrival(self,customerID):
        
        self.totalCustomers = self.totalCustomers + 1
        
        if(self.numServers- self.busyServers)>0: #If server available
            self.busyServers = self.busyServers + 1
            self.EventList.insertNewEvent('Departure', self.clock+self.rv.computeServiceTime(), customerID)
        else:
            if(len(self.queue)<self.queueLength):#If queue available
                self.queue.insert(0,customerID)
            else:
                self.blockedCustomers = self.blockedCustomers+1 #update blocked status
                events = self.EventList.getEvents(customerID)
                self.EventList.removeEvents(events)
                
        self.EventList.insertNewEvent('Arrival', self.clock+self.rv.getNextArrival(), customerID+1)
        
    #Routine to handle Event Departure
    def EventDeparture(self,customerID):
        self.busyServers = self.busyServers - 1    
                 
        if(self.queue != []): #If queue not empty
            #print("queue not emty")
            nextCustomerID = self.queue.pop()   #get next customer from queue
            self.busyServers = self.busyServers + 1 #serve the customer
            self.EventList.insertNewEvent('Departure', self.clock+self.rv.computeServiceTime(), nextCustomerID) #Update departure event
        
        events = self.EventList.getEvents(customerID)
        if(len(events)==2):
            self.responseTime.append(events[1].eventTime - events[0].eventTime) #Capture waiting time in the system
        self.EventList.removeEvents(events) #Release the memory
        
    #Routine to handle stopping condition for warm-up test
    def warmupStoppingCondition(self, simulationTime):
        return self.clock < (simulationTime+2) #buffer time
    
    #Routine to handle stopping condition for batch means technique
    def batchStoppingCondition(self):
        return self.batchIndex <= self.batchSize
    
    #Routine to get mean numbers of customers in a particular time interval
    def getMeanCustomers(self):
        tot_customers=0
        sum_time=0
        for i in range(0,len(self.customersState)-1):
            t1 = self.customersState[i].time
            t2 = self.customersState[i+1].time
            tot_customers = tot_customers + (self.customersState[i].numCustomers * (t2-t1)) 
            sum_time = sum_time + (t2-t1) 

        if(tot_customers!=0):
            result = tot_customers/sum_time
        else:
            result = 0
        return result

    #Routine to get customers in the system at every deltaT
    #Routine used to estimate the warm-up period
    def getCustomersAtEveryDeltaT(self, deltaT):
        numCustomers = []
        
        start = math.floor(self.customersState[0].time)
        end   = math.floor(self.customersState[len(self.customersState)-1].time)
        k=0
        for j in self.frange(start,end,deltaT):
            for i in range(k,len(self.customersState)):
                t1 = self.customersState[i].time
                if (i+1 >= len(self.customersState)):
                    t2 = j + deltaT
                else:
                    t2 = self.customersState[i+1].time
         
                if t1<=j and t2>j:
                    tot_customers = self.customersState[i].numCustomers
                    break
                k=k+1
            if(tot_customers!=0):
                numCustomers.append(tot_customers)       
            else:
                numCustomers.append(0)
        return numCustomers
    
    #Utility function 
    def frange(self,x, y, jump):
        while x < y:
            yield x
            x += jump


#Call the main module
main()


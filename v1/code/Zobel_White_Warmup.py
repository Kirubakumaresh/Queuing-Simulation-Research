
import math
import random
import numpy as np
import matplotlib.pyplot as plt

def main():
	#HW2 2.1
	findWarmupPeriod(arrivalRate=1/2,
					 serviceRate=1/1,
					 queueLength=5,
					 numServers=2,
					 numCustomersAtStart=0,
					 simulationTime=100,
					 numSimulations=1000,
                              collectionLength=10)
                              

def findWarmupPeriod(arrivalRate, serviceRate, queueLength, numServers, numCustomersAtStart, simulationTime, numSimulations, collectionLength):
    diffRateList = []
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
    
        startTime=1
        endTime=simulationTime
        diffRate = controller.getRateAtEveryDeltaT(startTime, endTime ,1,collectionLength)
        diffRateList.append(diffRate)
        n=n+1
    
    #Average on all the simulations and Plot the result
    diffRateArr = np.array(diffRateList)
    diffRateMean = np.mean(diffRateArr,axis=0) 
    diffRateSD = np.std(diffRateArr,axis=0) 
    diffRateErr = 1.96 * np.sqrt(diffRateSD*diffRateSD/len(diffRateArr))
    diffRateLower = diffRateMean - diffRateErr
    diffRateUpper = diffRateMean + diffRateErr
    diffRateFinal = np.logical_and(diffRateLower<0, diffRateUpper>0)
    index=np.argmax(diffRateFinal==True)
    print("warmup reached at time : " , index)
    print("mean : " , diffRateMean[index])
    print("SD : " , diffRateSD[index])
    print("LCL : " , diffRateLower[index])
    print("UCL : " , diffRateUpper[index])
    plt.errorbar(range(startTime,endTime),diffRateMean[0:simulationTime-startTime], yerr=diffRateErr)
    plt.ylim([-1,1])
    plt.ylabel('Mean of difference of arrival rate - departure rate')
    plt.show()    


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
        events = [self.Events[i] for i in range(len(self.Events)) if self.Events[i].customerID == _customerID]
        return events
        
    def getNumberofEvents(self, startTime, endTime, eventType):
        i = len(self.Events)-1
        eventCount=0
        while(i>0 and self.Events[i].eventTime >= startTime):
            if(self.Events[i].eventTime <= endTime and self.Events[i].eventType==eventType):
                eventCount=eventCount+1
            i=i-1
        return eventCount

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
        self.totalCustomers = 0
        self.blockedCustomers = 0
        self.clock=0
        
      
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
                #self.EventList.removeEvents(events)
                
        self.EventList.insertNewEvent('Arrival', self.clock+self.rv.getNextArrival(), customerID+1)
        
    #Routine to handle Event Departure
    def EventDeparture(self,customerID):
        self.busyServers = self.busyServers - 1    
                 
        if(self.queue != []): #If queue not empty
            #print("queue not emty")
            nextCustomerID = self.queue.pop()   #get next customer from queue
            self.busyServers = self.busyServers + 1 #serve the customer
            self.EventList.insertNewEvent('Departure', self.clock+self.rv.computeServiceTime(), nextCustomerID) #Update departure event
       
    #Routine to handle stopping condition for warm-up test
    def warmupStoppingCondition(self, simulationTime):
        return self.clock < (simulationTime+2) #buffer time
      
    def getRateAtEveryDeltaT(self, start, end , deltaT, timeWindow):
        diffRate = []
        for j in self.frange(start,end,deltaT):
            numArrivals = self.EventList.getNumberofEvents(j-timeWindow, j, "Arrival")
            numDepartures = self.EventList.getNumberofEvents(j-timeWindow, j, "Departure")
            arrivalRate = numArrivals / timeWindow
            departureRate = numDepartures / timeWindow
            diffRate.append(arrivalRate-departureRate)

        return diffRate
        
    #Utility function 
    def frange(self,x, y, jump):
        while x < y:
            yield x
            x += jump


#Call the main module
main()


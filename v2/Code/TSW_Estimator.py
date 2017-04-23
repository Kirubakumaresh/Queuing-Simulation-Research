
import math
import random
import numpy as np
import matplotlib.pyplot as plt
import os

def main():
	findWarmupPeriod(arrivalRate=1/2,
					  serviceRate=1/1,
					  queueLength=5,
					  numServers=2,
					  numCustomersAtStart=0,
					  simulationTime=100,
					  numSimulations=1)
                              

def findWarmupPeriod(arrivalRate, serviceRate, queueLength, numServers, numCustomersAtStart, simulationTime, numSimulations):
    random.seed(0) #to get the same results
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
    crossedList, diffRate = controller.getRateAtEveryDeltaT(startTime, endTime ,1)
    x = range(1,simulationTime)
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax1.plot(x, crossedList)
    ax1.set_ylabel("Number of Crossings of the mean")
    ax1.set_xlabel("Time")
    ax2 = fig.add_subplot(212)
    ax2.plot(x, diffRate)
    ax2.set_ylabel("arrivalRate - departureRate")
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

    def getEventsByType(self,_eventType):
        events = [self.Events[i] for i in range(len(self.Events)) if self.Events[i].eventType == _eventType]
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
       
    #Routine to handle stopping condition for warm-up test
    def warmupStoppingCondition(self, simulationTime):
        return self.clock < (simulationTime+2) #buffer time
        
    #Compute rate using TSW method
    #Section 2.1 of "Performance evaluation and comparison of four network packet rate estimators"
    def computeRate(self, currentTime, eventType):
        #print("start", eventType)
        win_length = 10
        avg_rate = 0.0
        t_front = 0.0
        for event in self.EventList.getEventsByType(eventType):
            if event.eventTime > currentTime:
                break
            pkts_in_tsw = avg_rate * win_length
            new_pkts = pkts_in_tsw + 1
            avg_rate = new_pkts / ( event.eventTime - t_front+win_length)
            t_front = event.eventTime
        return avg_rate
        
    #compute Crossings as per Section 2.5 of the paper by Mahajan and Ingalls
    #"Evaluation of methods used to detect warmup period in steady state sinulation"
    def computeCrossings(self, diffRate):
        crossData = []
        mean=0
        for i in range(0,len(diffRate)-1):
            if  ( diffRate[i] >mean and diffRate[i+1]<mean ) or ( diffRate[i]<mean and diffRate[i+1]>mean) :
                crossData.append(1.0)
            else:
                crossData.append(0.0)
        return sum(crossData)
        
    def getRateAtEveryDeltaT(self, start, end , deltaT):
        crossedList = []
        diffRate=[]
        for j in self.frange(start,end,deltaT):
            arrivalRate = self.computeRate(j,'Arrival')
            departureRate = self.computeRate(j,'Departure')
            diffRate.append(arrivalRate-departureRate)
            crossed = self.computeCrossings(diffRate)
            crossedList.append(crossed)
            print(j , round(arrivalRate,6), round(departureRate,6), round(arrivalRate-departureRate,6), crossed)            
        return crossedList, diffRate
        
    #Utility function 
    def frange(self,x, y, jump):
        while x < y:
            yield x
            x += jump


#Call the main module
main()


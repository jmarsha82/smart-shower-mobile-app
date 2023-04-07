'''
Wireless Sensor Network
Smart Shower
'''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime
import threading
import re
import pandas as pd 
import logging
import time
import json
import os
import test_binning_kbinsdis


# Create thread object for subscription service    
class CallbackContainer(object):
    
    # Instance Variables
    def __init__(self, client):
        self._client = client
        self._status = False
        self._temperature = -5.0
        self._time = ''
        self._tempTrigger = False
        self._statusTrigger = False
        self._notificationTrigger = True

    # Custom MQTT message callback for temperature being received from App
    def customCallback(self, client, userdata, message):
        topicContentsOne = json.loads(message.payload.decode('utf-8'))
        self._temperature = topicContentsOne['temperature']
        # Get object of current time
        now = datetime.now()
        current_minute = str(now.minute)
        # Calculate minute as percent of Hour
        percent_of_hour = 100 * int(current_minute)/int(60)
        rounded_percent = round(percent_of_hour,)
        percent_string = str(rounded_percent)
        if(len(percent_string) < 2):
            percent_string = '0' + percent_string
        current_time = str(now.hour) + '.' + percent_string
        self._time = current_time
        # Change trigger to publish temperature to shower
        self._tempTrigger = True
        print("Received Command App")

    # Custom MQTT message callback for status from shower being received
    def customCallbackStatus(self, client, userdata, message):
        print("Received Status from Pi")
        topicContents = json.loads(message.payload.decode('utf-8'))
        self._status = topicContents['status']
        # Change trigger to publish shower status to app and notification logic
        self._statusTrigger = True
        self._notificationTrigger = True
        print("Sent Status to App")
    
    # Getters and Setters

    def getTempTrigger(self):
        return self._tempTrigger

    def setTempTrigger(self,tempSet):
        self._tempTrigger = tempSet

    def getStatusTrigger(self):
        return self._statusTrigger

    def setStatusTrigger(self,statusSet):
        self._statusTrigger = statusSet

    def getNotificationTrigger(self):
        return self._notificationTrigger

    def setNotificationTrigger(self,notificationSet):
        self._notificationTrigger = notificationSet

    def getTemperature(self):
        return self._temperature
    
    def getTime(self):
        return self._time

    def getStatus(self):
        return self._status

# Setup AWS IoT
# Connection settings
# host = <INSERT_HOST>
# rootCAPath = <INSERT_PATH>
# certificatePath = <INSERT_PATH>
# privateKeyPath = <INSERT_PATH>
port = 8883
clientId = "shower_test_ec2"
controlTopic = "$aws/things/shower_start_cloud/shadow/update"
controlTopicPi = "$aws/things/shower_start_pi/shadow/update"
controlTopicStatus = "$aws/things/shower_status_pi/shadow/update"
controlTopicStatusPc = "$aws/things/shower_status_pc/shadow/update"
controlTopicAppNotification = "$aws/things/shower_app_notification/shadow/update"

# Init AWSIoTMQTTClient object
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(
    rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
# Infinite offline Publish queueing
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
myAWSIoTMQTTClient.connect()

myCallbackContainer = CallbackContainer(myAWSIoTMQTTClient)
# SUBSCRIBE Connect to AWS IoT topic of shower start command
myAWSIoTMQTTClient.subscribe(controlTopic, 1, myCallbackContainer.customCallback)
# SUBSCRIBE Connect to AWS IoT topic of shower ready command
myAWSIoTMQTTClient.subscribe(controlTopicStatus, 1, myCallbackContainer.customCallbackStatus)
time.sleep(2)
# Grab time and temp from test_binning_kbinsdis
notification_tuple = test_binning_kbinsdis.doBinning()

while True:
    if(myCallbackContainer.getNotificationTrigger()):
        print("Determining if notification should be sent")
        # Convert Time Back to regular format
        number_to_split = notification_tuple[0]
        convert_temp = int(notification_tuple[1])
        hour_place = int(notification_tuple[0])
        number_dec = str(number_to_split-int(number_to_split))[1:]
        minutes_place = round(60 * float(number_dec))
        bin_time = str(hour_place) + ":" + str(minutes_place)
        shower_time = datetime.now()
        formatted_shower_time = str(shower_time.hour) + ":" + str(shower_time.minute)
        # Checks current time against bin time to determine whether or not to publish 
        # print("Time we are sending a notification at = " + str(hour_place) + ":" + str(minutes_place))
        if(bin_time == formatted_shower_time):
            messageStatus = {}
            messageStatus['suggestedTime'] = str(hour_place) + ":" + str(minutes_place)
            messageStatus['suggestedTemp'] = str(convert_temp)
            messageJson = json.dumps(messageStatus)
            # Publish notification of time and temp to app with conditional is met
            myAWSIoTMQTTClient.publish(controlTopicAppNotification, messageJson, 1)
            myCallbackContainer.setNotificationTrigger(False)
            print("Notification Sent")
    if(myCallbackContainer.getTempTrigger()):
        message = {}
        message['temperature'] = str(myCallbackContainer.getTemperature())
        messageJson = json.dumps(message)
        # Publish temperature from app to shower
        myAWSIoTMQTTClient.publish(controlTopicPi, messageJson, 1)
        print("Temperature OR Stop " + str(myCallbackContainer.getTemperature()))
        myCallbackContainer.setTempTrigger(False)
    if(myCallbackContainer.getStatusTrigger()):
        messageStatus = {}
        messageStatus['status'] = 'true'
        messageJson = json.dumps(messageStatus)
        # Publish status of true to app from shower for status
        myAWSIoTMQTTClient.publish(controlTopicStatusPc, messageJson, 1)
        ## Log Requested Temperature sent from App only once to data set
        f = open('temperatures.txt','a')
        f.write(myCallbackContainer.getTemperature() + '\n')
        f.close()
        ## Write time shower turned on only once to data set
        g = open('time_data.txt','a')
        g.write(myCallbackContainer.getTime() + '\n')
        g.close()
        myCallbackContainer.setStatusTrigger(False)
        print("Publishing to App")
    time.sleep(5)

## New logic to run mean on data set and sent
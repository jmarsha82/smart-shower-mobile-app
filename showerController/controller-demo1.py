#! /usr/bin/env python3
'''
* Wireless Sensor Networks
* Demo 1 - Shower Controller
'''

#######################
# Import Libraries #
#######################

# Import utility libs
import glob
import json
import logging
import time
import os
# Import AWS IoT Core lib
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
# Import Adafruit servo lib
from adafruit_servokit import ServoKit

############################
# Helper Functions/Classes #
############################

# Custom MQTT message callback
class CallbackContainer(object):

    # Constructor
    def __init__(self, client):
        self._client = client
        self._state = False

    # Shower control topic callback function
    def shower_control_callback(self, client, userdata, message):
        topic_contents = json.loads(message.payload.decode('utf-8'))
        if(topic_contents['state']['reported']['command'] == 'start'):
            self._state = True
        elif(topic_contents['state']['reported']['command'] == 'stop'):
            self._state = False

    # Accessor function
    def get_state(self):
        return self._state

# Get raw data from temp sensor
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

# Parse raw data from temp sensor, validate, and extract temp
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f

####################
# Initialize Servo #
####################
kit = ServoKit(channels = 16)
kit.servo[0].set_pulse_width_range(500, 2500)
kit.servo[0].actuation_range = 270
kit.servo[0].angle = 0
servo_angle = 0
forward = True

##########################
# Initialize Temp Sensor #
##########################
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'
temp_list = []
init_temp = read_temp()
temp_list.append(init_temp)
temp_list.append(init_temp)
temp_list.append(init_temp)
temp_list.append(init_temp)
temp_list.append(init_temp)

#################
# Setup AWS IoT #
#################
# Configure AWS IoT connection settings
# host = <INSERT_HOST>
# rootCAPath = <INSERT_PATH>
# certificatePath = <INSERT_PATH>
# privateKeyPath = <INSERT_PATH>
port = 8883
client_id = "shower_controller"
status_topic = "$aws/things/shower_status_pi/shadow/update"
control_topic = "$aws/things/shower_start_pi/shadow/update"

# Configure AWS IoT logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Init AWSIoTMQTTClient
my_iot_client = AWSIoTMQTTClient(client_id)
my_iot_client.configureEndpoint(host, port)
my_iot_client.configureCredentials(root_CA_path, private_key_path, certificate_path)

# Configure AWSIoTMQTTClient connection settings
my_iot_client.configureAutoReconnectBackoffTime(1, 32, 20)
my_iot_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_iot_client.configureDrainingFrequency(2)  # Draining: 2 Hz
my_iot_client.configureConnectDisconnectTimeout(10)  # 10 sec
my_iot_client.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
my_iot_client.connect()

# Subscribe to control topic
my_callback_container = CallbackContainer(my_iot_client)
my_iot_client.subscribe(control_topic, 1, my_callback_container.shower_control_callback)

time.sleep(2)
print('System initialization complete.')

########################
# Main Processing Loop #
########################

while True:
    # Publish glove data topic when control topic says start until control topic says stop
    if(my_callback_container.get_state()):
        # Wiggle servo back and forth
        if servo_angle == 270:
            forward = False

        if servo_angle == 0:
            forward = True

        if forward == True:
            servo_angle += 90
        else:
            servo_angle -= 90

        kit.servo[0].angle = servo_angle

        # Get current temp and calculate average over last 5 seconds
        avg_temp = 0.0
        cur_temp = read_temp()

        temp_list.pop(0)
        temp_list.append(cur_temp)

        avg_temp = sum(temp_list) / len(temp_list)

        # Build data topic
        message = {}
        message['state'] = {}
        message['state']['reported'] = {}
        message['state']['reported']['temperature'] = avg_temp
        message_json = json.dumps(message)

        # Publish data topic
        my_iot_client.publish(status_topic, message_json, 1)

        print('Angle: %d degrees, Temp: %.2f*F' % (servo_angle, avg_temp))

    time.sleep(1)

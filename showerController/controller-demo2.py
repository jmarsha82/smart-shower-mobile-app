#! /usr/bin/env python3
'''
* CSE521 Wireless Sensor Networks
* Demo 2 - Shower Controller
* Jeremy Manin
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
# Import PID library
from simple_pid import PID

############################
# Helper Functions/Classes #
############################

# Custom MQTT message callback
class CallbackContainer(object):

    # Constructor
    def __init__(self, client):
        self._client = client
        self._setpoint = 0.0
        self._setpoint_trigger = False
        self._active = False

    # Shower control topic callback function
    def shower_control_callback(self, client, userdata, message):
        topic_contents = json.loads(message.payload.decode('utf-8'))
        recvd = topic_contents['temperature']
        if recvd == 'stop':
            self._active = False
        else:
            self._active = True
            self._setpoint = float(recvd)
            self._setpoint_trigger = True

    # Accessor functions
    def get_setpoint(self):
        return self._setpoint

    def get_setpoint_trigger(self):
        return self._setpoint_trigger

    def get_active(self):
        return self._active

    # Mutator functions
    def reset_setpoint_trigger(self):
        self._setpoint_trigger = False

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
kit.servo[15].set_pulse_width_range(500, 2500)
kit.servo[15].actuation_range = 270
kit.servo[15].angle = 270
servo_angle = 270

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

##################
# Initialize PID #
##################
pid = PID(3, 0.02, 0, setpoint = my_callback_container.get_setpoint())
pid.output_limits = (90, 270)

time.sleep(2)
print('System initialization complete.')

########################
# Main Processing Loop #
########################

while True:
    # Re-initialize PID when new setpoint topic is received
    if my_callback_container.get_setpoint_trigger():
        my_callback_container.reset_setpoint_trigger()
        pid = PID(3, 0.02, 0, setpoint = my_callback_container.get_setpoint())
        pid.output_limits = (90, 270)
        kit.servo[15].angle = 135

    if my_callback_container.get_active():
        # Get current temp and calculate average over last 5 seconds
        avg_temp = 0.0
        cur_temp = read_temp()

        temp_list.pop(0)
        temp_list.append(cur_temp)

        avg_temp = sum(temp_list) / len(temp_list)

        # Get new servo position from PID
        # Need to flip, round, and bounds-check outout
        # (Servo 270 = off, PID 0 = off)
        servo_angle = pid(avg_temp)
        servo_angle = round(abs(servo_angle-270))

        if servo_angle > 270:
           servo_angle = 270

        if servo_angle < 0:
           servo_angel = 0

        kit.servo[15].angle = servo_angle

        if round(avg_temp) == round(my_callback_container.get_setpoint()):
            # Build data topic
            message = {}
            message['status'] = 'true'
            message_json = json.dumps(message)

            # Publish data topic
            my_iot_client.publish(status_topic, message_json, 1)

        print('Angle: %d degrees, Temp: %.2f*F' % (servo_angle, avg_temp))
    # Command shower off if system is inactive
    else:
        kit.servo[15].angle = 270

    time.sleep(1)

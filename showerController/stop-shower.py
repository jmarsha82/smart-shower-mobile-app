# Stops the shower
from adafruit_servokit import ServoKit
kit = ServoKit(channels = 16)
kit.servo[15].set_pulse_width_range(500, 2500)
kit.servo[15].actuation_range = 270
kit.servo[15].angle = 270

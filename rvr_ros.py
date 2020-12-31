import os
import sys

import asyncio
from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RvrStreamingServices

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from std_msgs.msg import Int8MultiArray
from geometry_msgs.msg import Vector3
from geometry_msgs.msg import Twist


import time

import json

debug = True

rvr = SpheroRvrObserver()

# sensor variable initialization
imu_global = {}
color_global = {}
accelerometer_global = {}
ambient_global = {}
encoder_global = {}

received = 0x00     # received byte - fully received at 0x1f

# send stuff variable initialization


# sensor publisher
class rvrNode(Node):

    def __init__(self):
        super().__init__('sphero_node')
        self.publisher_ = self.create_publisher(
            String,
            'sensors',  # publish to sensorsr channel
            10)

        self.subscription = self.create_subscription(
            Twist,
            'drive',   # listen on drive channel
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def send(self, message):
        msg = String()
        msg.data = message
        self.publisher_.publish(msg)
        # if debug: self.get_logger().info('Publishing: "%s"' % msg.data)

    def listener_callback(self, msg):
        if debug: print("heard")

        linear = msg.data.linear
        angular = msg.data.angular

        rvr.drive_tank_normalized(
            left_velocity=drive_data[0],    # left motor control
            right_velocity=drive_data[1]    # right motor control
        )

        if debug: print(str(drive_data))


rclpy.init(args=None)
ros = rvrNode()

# Check if all values are collected
def checkData():
    global received
    if received == 31:
        received = 0
        ros.send(
            json.dumps({
                    **imu_global,
                    **color_global,
                    **accelerometer_global,
                    **ambient_global,
                    **encoder_global
            })
        )
        #if debug: print('publish')



def imu_handler(imu_data):
    #print('IMU data response: ', imu_data)
    #if debug: print('IMU data received')
    global imu_global
    global received
    imu_global = imu_data
    received = received | (1)
    #print(received)
    checkData()


def color_detected_handler(color_detected_data):
    #print('Color detection data response: ', color_detected_data)
    #if debug: print('Color detection data received')
    global color_global
    global received
    color_global = color_detected_data
    received = received | (1 << 1)
    #print(received)
    checkData()


def accelerometer_handler(accelerometer_data):
    #print('Accelerometer data response: ', accelerometer_data)
    #if debug: print('Accelerometer data received')
    global accelerometer_global
    global received
    accelerometer_global = accelerometer_data
    received = received | (1 << 2)
    #print(received)
    checkData()


def ambient_light_handler(ambient_light_data):
    #print('Ambient light data response: ', ambient_light_data)
    #if debug: print('Ambient light data received')
    global ambient_global
    global received
    ambient_global = ambient_light_data
    received = received | (1 << 3)
    #print(received)
    checkData()

def encoder_handler(encoder_data):
    #print('Encoder data response: ', encoder_data)
    #if debug: print('Encoder data received')
    global encoder_global
    global received
    encoder_global = encoder_data
    received = received | (1 << 4)
    #print(received)
    checkData()

def will_sleep_handler():
    if debug: print("RVR going to sleep - sending wake signal")
    rvr.wake()

def main():
    """ This program demonstrates how to enable multiple sensors to stream.
    """

    try:
        rvr.wake()

        # Give RVR time to wake up
        time.sleep(2)

        if debug: print("Starting imu handler...")
        rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.imu,
            handler=imu_handler
        )
        if debug: print("Starting color handler...")
        rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.color_detection,
            handler=color_detected_handler
        )
        if debug: print("Starting accelerometer handler...")
        rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.accelerometer,
            handler=accelerometer_handler
        )
        if debug: print("Starting ambient light handler...")
        rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.ambient_light,
            handler=ambient_light_handler
        )
        if debug: print("Starting encoder handler...")
        rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.encoders,
            handler=encoder_handler
        )
        if debug: print("Starting sensor control...")

        #await rvr.sensor_control.start(interval=250)
        rvr.sensor_control.start(interval=1000)

        if debug: print("Starting keep awake...")
        rvr.on_will_sleep_notify(will_sleep_handler)

        #TODO: Battery state handler


        #TODO:

        while True:
            rclpy.spin_once(ros)


    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')

    finally:
        rvr.sensor_control.clear()

        # Delay to allow RVR issue command before closing
        time.sleep(.5)

        rvr.close()
    # The asyncio loop will run forever to allow infinite streaming.


if __name__ == '__main__':
    main()

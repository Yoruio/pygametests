from imutils.video import VideoStream
import argparse
import imutils

from pygame.locals import KEYDOWN, K_ESCAPE
import pygame
import cv2
import sys
import time

''' ROS STUFF
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8MultiArray
from geometry_msgs.msg import Vector3
from geometry_msgs.msg import Twist
'''


# setup

# Class Fps
# Just a simple class to calculate FPS values between frames.
class Fps:
    prev_time = None
    curr_fps = None
    framerate_buffer = []

    # smooth_fps gives fps as average of previous 10 frame times instead of instantaneous frame time
    smooth_fps = None

    def __init__(self, smooth=False):
        self.prev_time = time.time()
        self.curr_fps = 0
        self.smooth = smooth

    # update()
    # function that updates frame time and returns fps
    def update(self):
        curr_time = time.time()
        self.curr_fps = int(1 / (curr_time - self.prev_time))
        self.prev_time = curr_time
        if self.smooth:
            self.framerate_buffer.append(self.curr_fps)
            if len(self.framerate_buffer) > 10:
                self.framerate_buffer.pop()
            self.smooth_fps = sum(self.framerate_buffer) / len(self.framerate_buffer)
            return self.smooth_fps
        else:
            return self.curr_fps

    # fps()
    # simple getter function for FPS values
    def fps(self, smooth=None):
        if smooth is None:
            smooth = self.smooth
        if smooth:
            return self.smooth_fps
        else:
            return self.curr_fps


''' ROS STUFF
class RosPublisher(Node):
    def __init__(self):
        super().__init__('ros_publisher')
        self.publisher_ = self.create_publisher(Vector3, 'drive', 10)

'''
'''
    def send(self, data):
        msg = Int8MultiArray()
        msg.data = data
        self.publisher_.publish(msg)
        self.get_logger().info('publishing "%d"' % msg.data)
'''
'''

    def send(self, forward, turn):
        msg = Twist()
        linear = Vector3()
        linear.z = 0 - forward
        linear.x = 0
        linear.y = 0
        angular = Vector3()
        angular.y = turn
        angular.x = 0
        angular.z = 0
        msg.data.linear = linear
        msg.data.angular = angular
        self.publisher_.publish(msg)
'''


def main():
    print("enter main")
    white = (255, 255, 255)
    green = (0, 255, 0)
    blue = (0, 0, 128)
    red = (255, 0, 0)

    background_colour = white

    # some settings
    # width and height of capture and fullscreen resolution
    (width, height) = (1280, 720)
    # dimensions of initial bounding box
    init_bb_dim = (100, 100)
    # PID constant for Potential and derivative
    (kp, kd) = (1, 1/3)
    # This just inverts the drive numbers to match scientific axis
    (kp, kd) = (-kp, -kd)

    ''' ROS STUFF
    print("init ROS")
    rclpy.init()
    ros = RosPublisher()
    '''

    # screen = pygame.display.set_mode((width, height))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_mode((width, height), pygame.FULLSCREEN)
    sw, sh = pygame.display.get_surface().get_size()
    (cw, ch) = (sw, sh)

    print("init pygame")
    pygame.init()
    pygame.display.set_caption('Object tracking')
    screen.fill(background_colour)
    pygame.display.flip()

    comic_sans = pygame.font.Font('COMIC.TTF', 32)

    print("init video capture")
    cap = cv2.VideoCapture(0)
    print("set width")
    cap.set(3, cw)
    print('set height')
    cap.set(4, ch)

    print("init misc variables")
    # initial bounding box
    bb = None
    cursor_pos = None

    # bounding box to draw around tracked object
    bounding_box = None
    prev_bounding_box = None
    tracking_error = False

    fps_counter = Fps(True)

    # CV STUFF
    tracker_type = "medianflow"
    OPENCV_OBJECT_TRACKERS = {
        "csrt": cv2.TrackerCSRT_create,  # good accuracy, bad failure report, slow
        "kcf": cv2.TrackerKCF_create,  # loses traction
        "boosting": cv2.TrackerBoosting_create,  # honestly horrible in every way
        "mil": cv2.TrackerMIL_create,  # also horrible in every way
        "tld": cv2.TrackerTLD_create,  # VERY good accuracy, long term but extremely slow
        "medianflow": cv2.TrackerMedianFlow_create,  # really good tracking but drifts
        "mosse": cv2.TrackerMOSSE_create  # can't go fast
    }
    tracker = OPENCV_OBJECT_TRACKERS[tracker_type]()

    frame_center = (cw / 2, ch / 2)
    try:

        while True:
            ret, orig_frame = cap.read()
            orig_frame = cv2.flip(orig_frame, 0)
            orig_frame = cv2.resize(orig_frame, (sw, sh))

            frame = cv2.cvtColor(orig_frame, cv2.COLOR_BGR2RGB)
            frame = frame.swapaxes(0, 1)

            pygame.surfarray.blit_array(screen, frame)

            fps_text = comic_sans.render('FPS: %d' % fps_counter.update(), True, green)
            fps_rect = fps_text.get_rect()
            fps_rect.topleft = (0, 0)
            screen.blit(fps_text, fps_rect)

            # draw cursor
            if cursor_pos is not None:
                pygame.draw.rect(screen, blue, cursor_pos + init_bb_dim, 3)
                cursor_pos = None

            # draw bounding box
            if bb is not None:
                (success, box) = tracker.update(orig_frame)
                if success:
                    (x, y, w, h) = [int(v) for v in box]
                    prev_bounding_box = bounding_box
                    bounding_box = (x, y, w, h)
                    tracking_error = False
                else:
                    tracking_error = True

            if bounding_box is not None:
                if not tracking_error:
                    pygame.draw.rect(screen, green, bounding_box, 3)
                else:
                    pygame.draw.rect(screen, red, bounding_box, 3)

            # draw drive control
            if (bounding_box is not None) and (not tracking_error):
                box_center = (
                    (bounding_box[0] + bounding_box[2] / 2),
                    (bounding_box[1] + bounding_box[3] / 2)
                )
                prev_box_center = None if prev_bounding_box is None else (
                    (prev_bounding_box[0] + prev_bounding_box[2] / 2),
                    (prev_bounding_box[1] + prev_bounding_box[3] / 2)
                )
                # Proportional
                box_center = (
                    (bounding_box[0] + bounding_box[2] / 2),
                    (bounding_box[1] + bounding_box[3] / 2)
                )
                p = box_center[0] - frame_center[0]

                # Derivative
                d = 0 if prev_box_center is None else \
                    (box_center[0] - frame_center[0]) - (prev_box_center[0] - frame_center[0])

                angular_correction = kp * p + kd * d

                # print motor text
                motor_text = comic_sans.render('p: %d | d: %d | angular correction: %d' % (p, d, angular_correction), True,
                                               green)
                motor_rect = fps_text.get_rect()
                motor_rect.topleft = (0, 50)
                screen.blit(motor_text, motor_rect)

                ''' ROS STUFF
                # send correction value to ROS
                # this needs to be implemented in the ros2-rvr interface - rvr_ros.py
                # first value - forward - should probably have this change algorithmically somehow...
                # second value - angular
                ros.send(100, angular_correction)
                '''

            pygame.display.update()

            # Process user interaction
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    cursor_pos = (pos[0] - init_bb_dim[0] / 2, pos[1] - init_bb_dim[1] / 2)

                # if buttons are added to the interface, add them here.
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    cursor_pos = (pos[0] - init_bb_dim[0] / 2, pos[1] - init_bb_dim[1] / 2)
                    bb = cursor_pos + init_bb_dim
                    tracker = OPENCV_OBJECT_TRACKERS[tracker_type]()
                    tracker.init(orig_frame, bb)

                elif event.type == pygame.QUIT:
                    sys.exit(0)
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        sys.exit(0)

            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                cursor_pos = (pos[0] - init_bb_dim[0] / 2, pos[1] - init_bb_dim[1] / 2)

    except (KeyboardInterrupt, SystemExit):
        pygame.quit()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()

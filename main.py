from imutils.video import VideoStream
import argparse
import imutils

from pygame.locals import KEYDOWN, K_ESCAPE
import pygame
import cv2
import sys
import time


# setup


class Fps:
    prev_time = None
    curr_fps = None
    framerate_buffer = []
    smooth_fps = None

    def __init__(self, smooth=False):
        self.prev_time = time.time()
        self.curr_fps = 0
        self.smooth = smooth

    def update(self):
        curr_time = time.time()
        self.curr_fps = int(1 / (curr_time - self.prev_time))
        self.prev_time = curr_time
        self.framerate_buffer.append(self.curr_fps)
        if len(self.framerate_buffer) > 10:
            self.framerate_buffer.pop()
        if self.smooth:
            self.smooth_fps = sum(self.framerate_buffer) / len(self.framerate_buffer)
            return self.smooth_fps
        else:
            return self.curr_fps

    def fps(self):
        return self.curr_fps


def main():
    print("enter main")
    white = (255, 255, 255)
    green = (0, 255, 0)
    blue = (0, 0, 128)
    red = (255, 0, 0)

    background_colour = white

    # screen = pygame.display.set_mode((width, height))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
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
    cap.set(3, 1280)
    print('set height')
    cap.set(4, 720)

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

    frame_center = (cw/2, ch/2)
    try:

        while True:
            print("start loop")
            ret, orig_frame = cap.read()
            orig_frame = cv2.resize(orig_frame, (sw, sh))

            frame = cv2.cvtColor(orig_frame, cv2.COLOR_BGR2RGB)
            frame = frame.swapaxes(0, 1)

            pygame.surfarray.blit_array(screen, frame)

            fps_text = comic_sans.render('FPS: %d' % fps_counter.update(), True, green)
            fps_rect = fps_text.get_rect()
            fps_rect.topleft = (0, 0)
            screen.blit(fps_text, fps_rect)

            print("draw cursor")
            # draw cursor
            if cursor_pos is not None:
                pygame.draw.rect(screen, blue, cursor_pos + (50, 50), 3)
                cursor_pos = None

            print("draw bounding box")
            # draw bounding box
            if bb is not None:
                (success, box) = tracker.update(orig_frame)
                if success:
                    (x, y, w, h) = [int(v) for v in box]
                    prev_bounding_box = bounding_box
                    bounding_box = (x, y, w, h)
                else:
                    tracking_error = True

            if bounding_box is not None:
                if tracking_error:
                    pygame.draw.rect(screen, green, bounding_box, 3)
                else:
                    pygame.draw.rect(screen, red, bounding_box, 3)

            '''
            # draw drive control
            if (bounding_box is not None) and (not tracking_error):
                box_center = (
                    (bounding_box[0] + bounding_box[2] / 2),
                    (bounding_box[1] + bounding_box[3] / 2)
                )
                prev_box_center = (
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
                d = prev_bounding_box[0] - bounding_box[0]

                motor_control = p + 1/3 * d

                # print motor text
                motor_text = comic_sans.render('motor_control: %d' % motor_control, True, green)
                motor_rect = fps_text.get_rect()
                motor_rect.topleft = (0, 50)
                screen.blit(motor_text, motor_rect)
                '''



            pygame.display.update()

            # Process user interaction
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    cursor_pos = (pos[0] - 25, pos[1] - 25)
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    cursor_pos = (pos[0] - 25, pos[1] - 25)
                    bb = cursor_pos + (50, 50)
                    tracker = OPENCV_OBJECT_TRACKERS[tracker_type]()
                    tracker.init(orig_frame, bb)

                elif event.type == pygame.QUIT:
                    sys.exit(0)
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        sys.exit(0)

            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                cursor_pos = (pos[0] - 25, pos[1] - 25)

    except (KeyboardInterrupt, SystemExit):
        pygame.quit()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()

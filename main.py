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
    white = (255, 255, 255)
    green = (0, 255, 0)
    blue = (0, 0, 128)

    background_colour = white

    # screen = pygame.display.set_mode((width, height))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    sw, sh = pygame.display.get_surface().get_size()
    (cw, ch) = (sw, sh)

    pygame.init()
    pygame.display.set_caption('Object tracking')
    screen.fill(background_colour)
    pygame.display.flip()

    comic_sans = pygame.font.Font('COMIC.TTF', 32)

    cap = cv2.VideoCapture(0)
    cap.set(3, cw)
    cap.set(4, ch)

    bb_pos = None
    bb = None
    cursor_pos = None

    fps_counter = Fps(True)

    # CV STUFF
    tracker_type = "medianflow"
    OPENCV_OBJECT_TRACKERS = {
        "csrt": cv2.TrackerCSRT_create,  # good accuracy, bad failure report, slow
        "kcf": cv2.TrackerKCF_create,  # loses traction
        "boosting": cv2.TrackerBoosting_create, # honestly horrible in every way
        "mil": cv2.TrackerMIL_create,  # also horrible in every way
        "tld": cv2.TrackerTLD_create,  # VERY good accuracy, long term but extremely slow
        "medianflow": cv2.TrackerMedianFlow_create,  # really good tracking but drifts
        "mosse": cv2.TrackerMOSSE_create  # can't go fast
    }
    tracker = OPENCV_OBJECT_TRACKERS[tracker_type]()

    try:

        while True:

            ret, orig_frame = cap.read()
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
                pygame.draw.rect(screen, blue, cursor_pos + (50, 50), 3)
                cursor_pos = None

            # draw bounding box
            if bb is not None:
                (success, box) = tracker.update(orig_frame)
                if success:
                    (x, y, w, h) = [int(v) for v in box]
                    pygame.draw.rect(screen, green, (x, y, w, h), 3)
                else:
                    fail_text = comic_sans.render('rip failed', True, green)
                    fail_rect = fps_text.get_rect()
                    fail_rect.topleft = (0, 50)
                    screen.blit(fail_text, fail_rect)
                    # tracker = OPENCV_OBJECT_TRACKERS["kcf"]()

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

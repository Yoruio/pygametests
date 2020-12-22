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
    (width, height) = (1280, 720)

    # screen = pygame.display.set_mode((width, height))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    sw, sh = pygame.display.get_surface().get_size()

    pygame.init()
    pygame.display.set_caption('Object tracking')
    screen.fill(background_colour)
    pygame.display.flip()

    comic_sans = pygame.font.Font('COMIC.TTF', 32)
    text = comic_sans.render('haha pepe funny', True, green)
    textRect = text.get_rect()

    peep = pygame.image.load('peep.png')
    peep = pygame.transform.scale(peep, (100, 100))

    cap = cv2.VideoCapture(0)
    cap.set(3, sw)
    cap.set(4, sh)

    cursor_pos = (0, 0)

    fps_counter = Fps(True)
    try:

        while True:

            ret, frame = cap.read()
            frame = cv2.resize(frame, (sw, sh))
            textRect.topleft = (200, 100)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame.swapaxes(0, 1)

            pygame.surfarray.blit_array(screen, frame)
            # screen.blit(text, textRect)
            # screen.blit(peep, (50, 50))

            fps_text = comic_sans.render('FPS: %d' % fps_counter.update(), True, green)
            fps_rect = fps_text.get_rect()
            fps_rect.topleft = (0, 0)
            screen.blit(fps_text, fps_rect)

            pygame.draw.rect(screen, blue, cursor_pos + (50, 50), 3)

            pygame.display.update()



            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    cursor_pos = (pos[0] - 5, pos[1] - 5)

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

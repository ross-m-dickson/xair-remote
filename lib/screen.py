"""
This module holds the state of the touch screen and buttons
"""
import os
import threading
import datetime
import subprocess

import pygame
from gpiozero import Button

import xair_remote

class GPIOButton:
    """Stores a GPIO button, its state, and the event callback function."""
    page = 0
    pos = 0
    screen = None
    rec_proc = None
    debug = False

    def __init__(self, number, pos, ctl):
        self.debug = ctl.debug
        if self.debug:
            print("Start button Init")
        self.button_gpio = Button(number)
        self.pos = pos
        self.event_obj = pygame.event.Event(pygame.USEREVENT + 1 + pos,
                                            message="Button %d" % pos)
        if self.debug:
            print("after pygame event id")
        self.button_gpio.when_pressed = self.button_callback
        self.screen = ctl
        self.disable = [1, 1, 1]
        self.image = []
        if self.debug:
            print("finish button Init")

    def button_callback(self):
        """Callback for when button event triggers."""
        if self.debug:
            print("button_callback %d %d %d" % (self.pos, self.page, self.disable[self.page]))
        if self.disable[self.page] == 0:
            self.disable[self.page] = 1
            self.screen.button_function(self.pos, self.page, False)
        else:
            self.disable[self.page] = 0
            self.screen.button_function(self.pos, self.page, True)
        self.screen.screen_loop()

    def set_disable(self, value):
        "set the curren disable value"
        self.disable[self.page] = value

    def get_disable(self):
        "return the curren disable value"
        return self.disable[self.page]

    def get_img(self):
        "return the image representing the current page"
        return self.image[self.page]

class Screen:
    """
    This stores the state associated with drawing elements on the screen. It
    also holds the function to draw the screen
    """

    # pointers to other modules
    xair_remote = None
    xair_thread = None
    read_proc = None

    # define names for numbers
    size = width, height = 320, 240
    white = 255, 255, 255
    yellow = 254, 255, 25
    black = 0, 0, 0
    red = 255, 0, 0
    yellow = 255, 255, 0
    green = 0, 255, 0
    blue = 26, 0, 255

    box_left = 10
    box_width = 210
    margin = box_left + 4
    title_center = (box_left + box_width)/2
    button_left = box_left * 1.5 + box_width
    button_width = 320 - button_left - box_left/2

    #define strings
    names = ("Bass", "Guitar", "Keys", "Sax", "Ross", "Raluca", "Butch", "Ors",
             "Itai", "Guest", "Guest", "Guest", "Kick", "Snare", "Toms", "Hat")
    words = []
    numbers = []
    mic = ("1/4", "1/4", "1/4", "pga", "cm", "58", "58", "ors",
           "any", "", "", "", "pga", "58", "akg", "akg")
    mics = []
    button_nm = ("Remote", "Record", "Screen Off", "Setup",
                 "WiFi", "Auto Level", "Quit", "Return",
                 "Confirm", "Confirm", "Return", "Return")

    def __init__(self, address, monitor, debug):
        # initialize the pygame infrastructure
        if debug:
            print("start screen init")
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        pygame.init()

        self.address = address
        self.monitor = monitor
        self.debug = debug
        self.my_env = os.environ.copy()
        self.my_env['AUDIODEV'] = 'hw:X18XR18,0'
        self.record_command = ['rec', '-q', '--buffer', '1048576', '-c', '18', '-b', '24']

        if self.debug:
            print("start pygame")
        # define pygame values
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
        self.screen = pygame.display.set_mode([320, 240], pygame.FULLSCREEN)
        # define font sizes
        if self.debug:
            print("start fonts")
        font = pygame.font.Font(None, 24)
        smfont = pygame.font.Font(None, 19)
        title_font = pygame.font.Font(None, 34)
        pygame.mouse.set_visible(False)

        if self.debug:
            print("create buttons")
        # initialize GPIO buttons
        self.gpio_button = (GPIOButton(17, 0, self), GPIOButton(22, 1, self),
                            GPIOButton(23, 2, self), GPIOButton(27, 3, self))

        if self.debug:
            print("start surfaces")
        #convert strings to surfaces
        self.title = title_font.render("X Air Control", 1, (self.blue))
        self.sub_title = font.render("Channel Setup", 1, (self.blue))
        for j in range(16):
            self.words.append(pygame.transform.rotate(font.render(self.names[j],
                                                                  1, (self.red)), 315))
            self.numbers.append(font.render("%02d" % (j+1), 1, (self.red)))
            self.mics.append(smfont.render(self.mic[j], 1, (self.red)))
        for i in range(4):
            for j in range(3):
                self.gpio_button[i].image.append(
                    font.render(self.button_nm[i+(j*4)], 1, (self.blue)))

        self.title_w, self.title_h = self.title.get_size()
        self.subtitle_w, self.subtitle_h = self.sub_title.get_size()
        self.num_w, self.num_h = self.numbers[7].get_size()
        if self.debug:
            print("finish screen init")

    def button_function(self, pos, page, start):
        "Start the function specified by the button and page"
        if pos == 0:
            if page == 0:
                if start:
                    # initialize XAir Remote
                    self.xair_remote = xair_remote.XAirRemote(self.address, self.monitor, self.debug)
                    if self.xair_remote.state is None or self.xair_remote.state.quit_called:
                        self.gpio_button[pos].disable[page] = 1
                    else:
                        self.xair_thread = threading.Thread(
                            target=self.xair_remote.xair.refresh_connection)
                else:
                    # end XAir Remote threads
                    if self.xair_remote is not None:
                        if (self.xair_remote.xair is not None and
                                self.xair_remote.xair.server is not None):
                            self.xair_remote.xair.server.shutdown()
                        if self.xair_remote.state is not None:
                            self.xair_remote.state.quit_called = True
                    if self.debug:
                        print("Shutdown complete")
            elif page == 1:
                print("start wifi")
            else: # page == 2:
                exit()
        elif pos == 1:
            if page == 0:
                if start:
                    if self.debug:
                        print("start record")
                    self.rec_proc = subprocess.Popen(self.record_command + \
                        ['/media/pi/USBTrav/%s.wav' % datetime.datetime.now().\
                            strftime("%Y-%m-%d-%H%M%S")], env=self.my_env)
                else:
                    self.rec_proc.terminate()
            elif page == 1:
                print("start auto level")
            else: # page == 2:
                exit()
        elif pos == 2:
            if page == 0:
                print("screen off")
            elif page == 1:
                # power off menu, change to page 2
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 2 # switch screen
            else: # page == 2:
                # return from power off menu, change to page 1
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 1 # switch screen
        else:
            if page == 0:
                # setup menu, disable page
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 1 # switch screen
            elif page == 1:
                # return from setup menu, change to page 0
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 0 # switch screen
            else: # page == 2:
                # return from power off menu, change to page 1
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 1 # switch screen

    def screen_loop(self):
        """Update the screen after an event."""
        if self.debug:
            print("start screen loop")
        # set the background
        self.screen.fill(self.black)
        pygame.draw.rect(self.screen, self.blue, (0, 0, 320, 240), 3) # outer border
        # draw titles
        self.screen.blit(self.title, (self.title_center-(self.title_w/2), 10))
        self.screen.blit(self.sub_title, (self.title_center-(self.subtitle_w/2), 40))
        # draw channel names
        pygame.draw.rect(self.screen, self.red, (self.box_left, 68, self.box_width, 170), 1)
        for j in range(8):
            self.screen.blit(self.numbers[j], (self.margin   + (j * self.box_width/8), 70))
            self.screen.blit(self.words[j], (self.box_left + (j * self.box_width/8),
                                             70+self.num_h))
            self.screen.blit(self.mics[j], (self.box_left + (j * self.box_width/8), 135))
            self.screen.blit(self.numbers[j+8], (self.margin   + (j * self.box_width/8), 155))
            self.screen.blit(self.words[j+8], (self.box_left + (j * self.box_width/8),
                                               155+self.num_h))
            self.screen.blit(self.mics[j+8], (self.box_left + (j * self.box_width/8), 220))
        # draw the buttons
        for j in range(4):
            pygame.draw.rect(self.screen, self.yellow,
                             (self.button_left, 5+(j*60), self.button_width, 50),
                             self.gpio_button[j].get_disable())
            self.screen.blit(self.gpio_button[j].get_img(), (self.button_left + 4, 30 + (j*60)))

        pygame.display.flip()
        if self.debug:
            print("finish screen loop")
#        sleep(5)

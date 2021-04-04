"""
This module holds the state of the touch screen and buttons
"""
import os
import threading
import pygame
#import subprocess

from gpiozero import Button

import xair_remote

class GPIOButton:
    """Stores a GPIO button, its state, and the event callback function."""
    page = 0
    pos = 0
    screen = None

    def __init__(self, number, pos, ctl):
        self.button_gpio = Button(number)
        self.pos = pos
        self.event_obj = pygame.event.Event(pygame.USEREVENT + 1 + pos,
                                            message="Button %d" % pos)
        self.button_gpio.when_pressed = self.button_callback
        self.screen = ctl
        self.disable = [1, 1, 1]

    def button_callback(self):
        """Callback for when button event triggers."""
        print("button_callback %d %d %d" % (self.pos, self.page, self.disable[self.page]))
        if self.disable[self.page] == 0:
            self.disable[self.page] = 1
            self.screen.button_function(self.pos, self.page, True)
        else:
            self.disable[self.page] = 0
            self.screen.button_function(self.pos, self.page, False)
        #self.screen.screen_loop()

    def set_disable(self, value):
        "set the curren disable value"
        self.disable[self.page] = value

    def get_disable(self):
        "return the curren disable value"
        return self.disable[self.page]

class Screen:
    """
    This stores the state associated with drawing elements on the screen. It
    also holds the function to draw the screen
    """

    # pointers to other modules
    xair_remote = None
    xair_thread = None
    osc_thread = None
    midi_thread = None

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
                 "WiFi", "Auto Level", "Power Off", "Return",
                 "Confirm", "Confirm", "Return", "Return")
    button_img = []

    def __init__(self, address, monitor, debug):
        # initialize the pygame infrastructure
        os.environ["SDL_FBDEV"] = "/dev/fb1"
        pygame.init()
        pygame.mouse.set_visible(False)

        # initialize XAir Remote
        self.xair_remote = xair_remote.XAirRemote(address, monitor, debug)

        # define pygame values
        self.screen = pygame.display.set_mode((320, 240))
        # define font sizes
        font = pygame.font.Font(None, 24)
        smfont = pygame.font.Font(None, 19)
        title_font = pygame.font.Font(None, 34)

        # initialize GPIO buttons
        self.gpio_button = (GPIOButton(17, 0, self), GPIOButton(22, 1, self),
                            GPIOButton(23, 2, self), GPIOButton(27, 3, self))

        #convert strings to surfaces
        self.title = title_font.render("X Air Control", 1, (self.blue))
        self.sub_title = font.render("Channel Setup", 1, (self.blue))
        for j in range(16):
            self.words.append(pygame.transform.rotate(font.render(self.names[j],
                                                                  1, (self.red)), 315))
            self.numbers.append(font.render("%02d" % (j+1), 1, (self.red)))
            self.mics.append(smfont.render(self.mic[j], 1, (self.red)))
        for j in range(12):
            self.button_img.append(font.render(self.button_nm[j], 1, (self.blue)))

        self.title_w, self.title_h = self.title.get_size()
        self.subtitle_w, self.subtitle_h = self.sub_title.get_size()
        self.num_w, self.num_h = self.numbers[7].get_size()

    def button_function(self, pos, page, start):
        "Start the function specified by the button and page"
        if pos == 0:
            if page == 0:
                if start:
                    xair_thread = threading.Thread(target=self.xair_remote.xair.refresh_connection)
                    osc_thread = xair_remote.XAirClient.worker
                    midi_thread = xair_remote.MidiController.worker
            elif page == 1:
                print("start wifi")
            else: # page == 2:
                print("power down")
        elif pos == 1:
            if page == 0:
                print("start record")
            elif page == 1:
                print("start auto level")
            else: # page == 2:
                print("power down")
        elif pos == 2:
            if page == 0:
                print("screen off")
            elif page == 1:
                print("Poweroff menu")
                # power off menu, change to page 2
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 2 # switch screen
            else: # page == 2:
                print("seup menu return")
                # return from power off menu, change to page 1
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 1 # switch screen
        else:
            if page == 0:
                # setup menu, disable page
                print("open setup menu")
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 1 # switch screen
            elif page == 1:
                # return from setup menu, change to page 0
                print("return from setup menu")
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 0 # switch screen
            else: # page == 2:
                # return from power off menu, change to page 1
                print("return from power off menu")
                self.gpio_button[pos].set_disable(1) # disable button
                for i in range(4):
                    self.gpio_button[i].page = 1 # switch screen

    def screen_loop(self):
        """Update the screen after an event."""
        while 1:
#            for event in pygame.event.get():
#                if event.type == pygame.QUIT: sys.exit()

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
                self.screen.blit(self.button_img[j], (self.button_left + 4, 30 + (j*60)))

            pygame.display.flip()

#starts the xair_remote
#the xair_recorder
#the WiFi as a server
#The fourth/bottom button opens a sub menu

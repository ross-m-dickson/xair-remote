"See help for main"
#!/usr/bin/env python3
import argparse

from time import sleep
from lib.screen import Screen


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description="""
    Configure a Raspberry PI to record 18 track audio from and control X-Air
    mixers with an X-Touch midi controller. This script assumes that the PI has
    a PiFIT or similar hat that provides a framebuffer and has buttons at GPIO
    17, 22, 23 and 27. Starting the app puts up a gui that is controlled by the
    buttons. Currently any touch screen capabilities are disabled.

    This descriptions assumes the PI is rotates with the HDMI and power ports at
    the top, the buttons on the right and Ethernet/USB ports on the left.

    The top/first button starts the xair_remote script, the second button starts
    the xair_recorder, the third button configures the WiFi as a server and
    enables a DHCP server on the wired Ethernet so that a connected XAir mixer
    doesn't need a static IP address. The fourth/bottom button opens a sub menu
    that includes an option to shut down the PI.

    The X-Touch is setup so that the encoders are configured as faders on any of
    10 banks with the first row of button configured as mutes for the selected
    bank. Banks are selected with the buttons in the lower row and the layer
    buttons. Most banks have two layers, the second access by pressing the
    button a second time, causing the button to blink. The fader is not used.
    Pressing an encoder returns the level to unity gain, not used for mic pre.
    """,
                                     epilog="""
    Bank 1-6 - Aux Bus 1-6 levels for Channels 1-8 and 9-16.
    Bank 7 - Aux Bus 7 aka FX 1 for Channels 1-8 and 9-16.
    Bank 8 - Mic PreAmp levels for Channels 1-8 and 9-16.
    Layer A - Main LR Mix levels of Channels 1-8 and 9-16 on second layer.
    Layer B - Aux Bus 1-6 output levels, USB IN Gain, Main/LR Bus output level.
    """,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    # the fader is not used as I don't have a good global use and a bank
    # specific use doesn't work well with a non moving fader
    PARSER.add_argument('xair_address', help='ip address of your X-Air mixer (optional)', nargs='?')
    PARSER.add_argument('-m', '--monitor',
                        help='monitor X-Touch connection and exit when disconnected',
                        action="store_true")
    PARSER.add_argument('-d', '--debug', help='enable debug output', action="store_true")
    PARSER.add_argument('-l', '--levels', help='get levels from the mixer', action="store_false")
    PARSER.add_argument('-c', '--clip', help='enabling auto leveling to avoid clipping',
                        action="store_true")
    PARSER.add_argument('-a', '--mac', help="use alternate mapping for mac", action="store_true")

    ARGS = PARSER.parse_args()

    SCREEN_OBJ = Screen(ARGS)
    SCREEN_OBJ.screen_loop()

    while SCREEN_OBJ is not None and SCREEN_OBJ.running:
        sleep(5)
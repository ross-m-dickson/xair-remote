"Starts an xAir remote, see main help string for more"
#!/usr/bin/env python3
import argparse
import threading
from lib.midicontroller import MidiController
from lib.xair import XAirClient, find_mixer
from lib.mixerstate import MixerState

class XAirRemote:
    "Initialize the XAir remote infrastructure"
    state = None
    midi = None
    xair = None

    def __init__(self, xair_address, a_monitor, debug, clip):
        if xair_address is None:
            address = find_mixer()
            if address is None:
                print('Error: Could not find any mixers in network.',
                      'Please specify ip address manually.')
                #return
                xair_address = "192.168.50.106"
            else:
                xair_address = address

        self.state = MixerState()
        self.midi = MidiController(self.state)
        self.state.midi_controller = self.midi
        if self.state.quit_called:
            return
        self.xair = XAirClient(xair_address, self.state)
        self.state.xair_client = self.xair
        self.xair.validate_connection()
        if self.state.quit_called:
            return

        self.state.debug = debug
        self.midi.debug = debug
        self.state.clip = clip

        if a_monitor:
            print('Monitoring X-Touch connection enabled')
            monitor = threading.Thread(target=self.midi.monitor_ports)
            monitor.daemon = True
            monitor.start()

        self.state.read_initial_state()
        self.midi.activate_bus(8)                    # set chanel level as initial bus

if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description="""
    Remote control X-Air mixers with an X-Touch midi controller.

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
    PARSER.add_argument('-c', '--clip', help='enabling auto leveling to avoid clipping',
                        action="store_true")
    ARGS = PARSER.parse_args()

    REMOTE = XAirRemote(ARGS.xair_address, ARGS.monitor, ARGS.debug, ARGS.clip)
    # now start polling refresh /xremote command while running
    REMOTE.xair.refresh_connection()

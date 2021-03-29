#!/usr/bin/env python3
import argparse
import threading
from lib.midicontroller import MidiController
from lib.xair import XAirClient, find_mixer
from lib.mixerstate import MixerState

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = """
    Remote control X-Air mixers with an X-Touch midi controller.

    The X-Touch is setup so that the encoders are configured as faders on any of
    10 banks with the first row of button configured as mutes for the selected
    bank. Banks are selected with the buttons in the lower row and the layer
    buttons. Most banks have two layers, the second access by pressing the
    button a second time, causing the button to blink. The fader is not used.
    Pressing an encoder returns the level to unity gain, not used for mic pre.
    """,
    epilog= """
    Bank 1-6 - Aux Bus 1-6 levels for Channels 1-8 and 9-16.
    Bank 7 - TBD
    Bank 8 - Mic PreAmp levels for Channels 1-8 and 9-16.
    Layer A - Main LR Mix levels of Channels 1-8 and 9-16 on second layer.
    Layer B - Aux Bus 1-6 output levels, USB IN Gain, Main/LR Bus output level.
    """,
    formatter_class=argparse.RawDescriptionHelpFormatter)
    # the fader is not used as I don't have a good global use and a bank
    # specific use doesn't work well with a non moving fader
    parser.add_argument('xair_address', help = 'ip address of your X-Air mixer (optional)', nargs = '?')
    parser.add_argument('-m', '--monitor', help='monitor X-Touch connection and exit when disconnected', action="store_true")
    parser.add_argument('-d', '--debug', help='enable debug output', action="store_true")
    args = parser.parse_args()

    if args.xair_address is None:
        address = find_mixer()
        if address is None:
            print('Error: Could not find any mixers in network. Please specify ip address manually.')
            exit()
        else:
            args.xair_address = address

    state = MixerState()
    midi = MidiController(state)
    state.midi_controller = midi
    xair = XAirClient(args.xair_address, state)
    state.xair_client = xair
    xair.validate_connection()

    state.debug = args.debug
    midi.debug = args.debug

    if args.monitor:
        print('Monitoring X-Touch connection enabled')
        monitor = threading.Thread(target = midi.monitor_ports)
        monitor.daemon = True
        monitor.start()
    
    state.read_initial_state()
    midi.activate_bus(8)                    # set chanel level as initial bus

    # now refresh /xremote command while running
    xair.refresh_connection()

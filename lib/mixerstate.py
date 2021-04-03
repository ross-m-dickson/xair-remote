"""
This module holds the mixer state of the X-Air device
"""

import time

class Channel:
    """
    Represents a single channel strip
    """
    def __init__(self, addr):
        self.fader = 0.0
        if addr.startswith('/ch'):
            # the 6 aux bus followed by the 4 effects
            self.sends = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.enables = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        else:
            self.sends = None
            self.enables = None
        self.ch_on = 1
        self.osc_base_addr = addr

class MixerState:
    """
    This stores the mixer state in the application. It also keeps
    track of the current selected fader bank on the midi controller to
    decide whether state changes from the X-Air device need to be
    sent to the midi controller.
    """
    debug = False

    fx_slots = [0, 0, 0, 0]

    active_bank = -1
    active_bus = -1

    # Each layer has 8 encoders and 8 buttons
    banks = [
        [
            Channel('/ch/01/mix'),
            Channel('/ch/02/mix'),
            Channel('/ch/03/mix'),
            Channel('/ch/04/mix'),
            Channel('/ch/05/mix'),
            Channel('/ch/06/mix'),
            Channel('/ch/07/mix'),
            Channel('/ch/08/mix')
        ],
        [
            Channel('/ch/09/mix'),
            Channel('/ch/10/mix'),
            Channel('/ch/11/mix'),
            Channel('/ch/12/mix'),
            Channel('/ch/13/mix'),
            Channel('/ch/14/mix'),
            Channel('/ch/15/mix'),
            Channel('/ch/16/mix')
        ],
        [
            Channel('/headamp/01'),
            Channel('/headamp/02'),
            Channel('/headamp/03'),
            Channel('/headamp/04'),
            Channel('/headamp/05'),
            Channel('/headamp/06'),
            Channel('/headamp/07'),
            Channel('/headamp/08')
        ],
        [
            Channel('/headamp/09'),
            Channel('/headamp/10'),
            Channel('/headamp/11'),
            Channel('/headamp/12'),
            Channel('/headamp/13'),
            Channel('/headamp/14'),
            Channel('/headamp/15'),
            Channel('/headamp/16')
        ],
        [
            Channel('/bus/1/mix'),
            Channel('/bus/2/mix'),
            Channel('/bus/3/mix'),
            Channel('/bus/4/mix'),
            Channel('/bus/5/mix'),
            Channel('/bus/6/mix'),
            Channel('/rtn/aux/mix'),
            Channel('/lr/mix')
        ]
    ]

    midi_controller = None
    xair_client = None

    def toggle_channel_mute(self, channel):
        """Toggle the state of a channel mute button."""
        if self.banks[self.active_bank][channel] is not None:
            if self.banks[self.active_bank][channel].ch_on == 1:
                self.banks[self.active_bank][channel].ch_on = 0
            else:
                self.banks[self.active_bank][channel].ch_on = 1
            self.xair_client.send(
                address=self.banks[self.active_bank][channel].osc_base_addr + '/on',
                param=self.banks[self.active_bank][channel].ch_on)
            self.midi_controller.set_channel_mute(
                channel, self.banks[self.active_bank][channel].ch_on)

    def toggle_send_mute(self, channel, bus):
        """Toggle the state of a send mute."""
        if self.debug:
            print('Toggle Send Mute %d %d' % (channel, bus))
        if ((self.banks[self.active_bank][channel] is not None)
                and self.banks[self.active_bank][channel].enables is not None):
            if self.banks[self.active_bank][channel].enables[bus] == 1:
                self.banks[self.active_bank][channel].enables[bus] = 0
                self.xair_client.send(
                    address=self.banks[self.active_bank][channel].osc_base_addr +
                    '/{:0>2d}/level'.format(bus + 1),
                    param=0.0)
            else:
                self.banks[self.active_bank][channel].enables[bus] = 1
                self.xair_client.send(
                    address=self.banks[self.active_bank][channel].osc_base_addr +
                    '/{:0>2d}/level'.format(bus + 1),
                    param=self.banks[self.active_bank][channel].sends[bus])
            self.midi_controller.set_channel_mute(channel, \
                self.banks[self.active_bank][channel].enables[bus])

    def change_fader(self, fader, delta):
        """Change the level of a fader."""
        if self.banks[self.active_bank][fader] is not None:
            self.banks[self.active_bank][fader].fader = \
                min(max(0.0, self.banks[self.active_bank][fader].fader + (delta / 200)), 1.0)
            self.xair_client.send(
                address=self.banks[self.active_bank][fader].osc_base_addr + '/fader',
                param=self.banks[self.active_bank][fader].fader)
            self.midi_controller.set_channel_fader(fader, self.banks[self.active_bank][fader].fader)

    def set_fader(self, fader, value):
        """Set the level of a fader."""
        if self.banks[self.active_bank][fader] is not None:
            self.banks[self.active_bank][fader].fader = value
            self.xair_client.send(
                address=self.banks[self.active_bank][fader].osc_base_addr + '/fader',
                param=self.banks[self.active_bank][fader].fader)
            self.midi_controller.set_channel_fader(fader, self.banks[self.active_bank][fader].fader)

    def change_bus_send(self, bus, channel, delta):
        """Change the level of a bus send."""
        if ((self.banks[self.active_bank][channel] is not None)
                and self.banks[self.active_bank][channel].sends is not None):
            self.banks[self.active_bank][channel].sends[bus] = \
                min(max(0.0, self.banks[self.active_bank][channel].sends[bus] + (delta / 200)), 1.0)
            self.xair_client.send(
                address=self.banks[self.active_bank][channel].osc_base_addr + \
                    '/{:0>2d}/level'.format(bus + 1),
                param=self.banks[self.active_bank][channel].sends[bus])
            self.midi_controller.set_channel_fader(channel, \
                self.banks[self.active_bank][channel].sends[bus])

    def set_bus_send(self, bus, channel, value):
        """Set the level of a bus send."""
        if ((self.banks[self.active_bank][channel] is not None)
                and self.banks[self.active_bank][channel].sends is not None):
            self.banks[self.active_bank][channel].sends[bus] = value
            self.xair_client.send(
                address=self.banks[self.active_bank][channel].osc_base_addr + \
                    '/{:0>2d}/level'.format(bus + 1),
                param=self.banks[self.active_bank][channel].sends[bus])
            self.midi_controller.set_channel_fader(channel, \
                self.banks[self.active_bank][channel].sends[bus])

    def change_headamp(self, fader, delta): # aka mic pre
        """Change the level of a mic pre aka headamp."""
        if self.banks[self.active_bank][fader] is not None:
            self.banks[self.active_bank][fader].fader = \
                min(max(0.0, self.banks[self.active_bank][fader].fader + (delta / 200)), 1.0)
            self.xair_client.send(
                address=self.banks[self.active_bank][fader].osc_base_addr + '/gain',
                param=self.banks[self.active_bank][fader].fader)
            self.midi_controller.set_channel_fader(fader, self.banks[self.active_bank][fader].fader)

    def received_osc(self, addr, value):
        """Process an OSC input."""
        for i in range(0, 5):
            for j in range(0, 8):
                if self.banks[i][j] is not None and addr.startswith(self.banks[i][j].osc_base_addr):
                    if addr.endswith('/fader'):     # chanel fader level
                        if self.debug:
                            print('Channel %s level %f' % (addr, value))
                        self.banks[i][j].fader = value
                        if i == self.active_bank and self.active_bus in [8, 9]:
                            self.midi_controller.set_ring(j, value)
                    elif addr.endswith('/on'):      # channel enable
                        if self.debug:
                            print('%s unMute %d' % (addr, value))
                        self.banks[i][j].ch_on = value
                        if i == self.active_bank and self.active_bus in [8, 9]:
                            self.midi_controller.set_channel_mute(j, value)
                    elif self.banks[i][j].sends is not None and addr.endswith('/level'):
                        if self.debug:
                            print('%s level %f' % (addr, value))
                        bus = int(addr[-8:-6]) - 1
                        self.banks[i][j].sends[bus] = value
                        if i == self.active_bank and bus == self.active_bus:
                            self.midi_controller.set_ring(j, value)
                    elif addr.endswith('/gain'):
                        if self.debug:
                            print('%s Gain level %f' % (addr, value))
                        self.banks[i][j].fader = value
                        if i == self.active_bank:   #doesn't need a bus check as only on one bus
                            self.midi_controller.set_ring(j, value)
                    break
            else:
                continue
            break

    def read_initial_state(self):
        """ Refresh state for all faders and mutes."""
        for i in range(0, 5):
            for j in range(0, 8):
                if self.banks[i][j] is not None:
                    if self.banks[i][j].osc_base_addr.startswith('/head'):
                        self.xair_client.send(address=self.banks[i][j].osc_base_addr + '/gain')
                        time.sleep(0.002)
                    else:
                        self.xair_client.send(address=self.banks[i][j].osc_base_addr + '/fader')
                        time.sleep(0.002)
                        self.xair_client.send(address=self.banks[i][j].osc_base_addr + '/on')
                        time.sleep(0.002)
                        if self.banks[i][j].sends is not None:
                            for k in range(len(self.banks[i][j].sends)):
                                self.xair_client.send(address=self.banks[i][j].osc_base_addr + \
                                    '/{:0>2d}/level'.format(k + 1))
                                time.sleep(0.002)

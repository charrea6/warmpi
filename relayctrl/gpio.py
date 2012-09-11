#!/usr/bin/env python

# Copyright (c) 2012 Ben Croston, Adam Charrett
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import atexit

__all__ = ['channel', 'IN', 'OUT', 'BOARD', 'BCM']

_BOARD_PINS = (None, None,  '0', None,  '1', None,  '4', '14', None, '15', '17', '18', '21',
               None, '22', '23', None, '24', '10', None,  '9', '25', '11',  '8', None,  '7')
_BCM_PINS = ('0', '1', '4', '7', '8', '9', '10', '11', '14', '15', '17', '18', '21', '22', '23', '24', '25')
_MODES = (BOARD, BCM) = range(2)

IN = 'in'
OUT = 'out'
GPIO_PATH = '/sys/class/gpio/'

_channels = {}

class InvalidChannelException(Exception):
    """The channel sent is invalid on a Raspberry Pi"""
    pass

class InvalidDirectionException(Exception):
    """An invalid direction was passed to setup()"""
    pass

class WrongDirectionException(Exception):
    """The GPIO channel has not been set up or is set up in the wrong direction"""
    pass

class InvalidModeException(Exception):
    """An invalid mode was passed to setmode()"""
    pass


def _get_sys_id(channel, mode):
    """Converts a channel identifer into the id used by the /sys interface"""
    # Ensure channel is an int
    try:
       channel = int(channel)
    except ValueError:
        raise InvalidChannelException("%r is not a valid channel id" % channel)

    if mode == BCM:
        value = str(channel)
        if value not in _BCM_PINS:
            raise InvalidChannelException("%d is not a valid GPIO channel" % channel)

    elif mode == BOARD:
        if (channel <= 0) or (channel > len(_BOARD_PINS)):
            raise InvalidChannelException("%d is not a valid channel number" % channel)

        # Pins start at 1, tuple is 0 indexed
        value = _BOARD_PINS[channel - 1]

        if value is None:
            raise InvalidChannelException("%d is not a valid GPIO channel" % channel)
    else:
        raise InvalidModeException("%r is not a valid mode" % mode)

    return value


class GPIOChannel(object):
    """Class used to manipulate/inspect a GPIO channel."""

    def __init__(self, id, direction):
        """Creates a new GPIO channel for the BCM id and direction specified."""
        self.__id = id
        self.__sys_id = GPIO_PATH + 'gpio%s/value' % id

        self.__fd = open(self.__sys_id, 'r' if direction == IN else 'w')
        self.__direction = direction

    @property
    def direction(self):
        """Returns the direction this channel is currently configured in."""
        return self.__direction

    @property
    def board_id(self):
        """Returns the board pin number of this channel"""
        return _BOARD_PINS.index(self.__id) + 1 # Add one as tupple is 0 indexed but pins start from 1.

    @property
    def id(self):
        """Returns the BCM id of this GPIO channel"""
        return int(self.__id)

    def output(self, bit):
        """Output a bit to this channel"""
        if self.__direction != OUT:
            raise WrongDirectionException("Attempt to output to an input channel!")

        self.__fd.write('1' if bit else '0')
        self.__fd.flush()

    def input(self):
        """Read a bit from this channel"""
        if self.__direction != IN:
            raise WrongDirectionException("Attempt to read from an output channel!")

        return self.__fd.read(1) == '1'

    def close(self):
        """Close this channel, allowing it to be opened in a different direction"""
        self.__fd.close()
        with open(GPIO_PATH + 'unexport', 'w') as f:
            f.write(self.__id)

        del _channels[self.__id]


def channel(channel, direction, mode=BOARD):
    """Returns a GPIOChannel object that can be used to manipulate or inspect the specified GPIO channel.

    channel is an integer that specifies the GPIO channel to return, depending on the value of
    mode this can be either BCM GPIO pin number or the Board pin number.
    direction is either IN or OUT.
    mode is the channel numbering mode being used, this is either BOARD for numbering based on
    the headers on the board or BCM for the BCM GPIO pin number.
    """
    sys_id = _get_sys_id(channel, mode)

    if sys_id in _channels:
        result = _channels[sys_id]
        if direction != result.direction:
            raise WrongDirectionException("Channel is already in use in a different direction")
    else:
        if os.path.exists(GPIO_PATH + 'gpio%s' % sys_id):
            # Channel is already exported, check that it is currently set for the
            # same direction as is being requested.
            with open(GPIO_PATH + 'gpio%s/direction' % sys_id) as f:
                current_direction = f.read()

            if current_direction.strip() != direction:
               # raise WrongDirectionException("Channel already exported and configured in a different direction!")
               with open('/sys/class/gpio/gpio%s/direction' % sys_id, 'w') as f:
                   f.write(direction)
        else:
            with open('/sys/class/gpio/export', 'w') as f:
                f.write(sys_id)

            with open('/sys/class/gpio/gpio%s/direction' % sys_id, 'w') as f:
                f.write(direction)

        result = GPIOChannel(sys_id, direction)
        _channels[sys_id] = result

    return result


# clean up routine
def _unexport():
    """Clean up by unexporting evey channel that we have set up"""
    for channel in _channels.values():
        channel.close()

atexit.register(_unexport)

if __name__ == '__main__':
    # assumes channel 11 INPUT
    #         channel 12 OUTPUT
    in_channel = channel(11, IN)
    out_channel = channel(12, OUT)
    print(in_channel.input())
    out_channel.output(True)

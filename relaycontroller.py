#!/usr/bin/python

import os
import pwd

from relayctrl.relay import Relay


RELAY_DIR = '/var/run/relay'

def setup():
    # Create run directory
    if not os.path.exists(RELAY_DIR):
        os.makedirs(RELAY_DIR)

    p = pwd.getpwnam('relay')
    os.chown(RELAY_DIR, p.pw_uid, p.pw_gid)

    # Drop privileges
    os.setgid(p.pw_gid)
    os.setuid(p.pw_uid)
    os.environ['USER'] = 'relay'
    os.environ['HOME'] = RELAY_DIR


if __name__ == '__main__':
    relays = {'HW':Relay(4), 'CH':Relay(17), 'CFH':Relay(21)}
    setup()

    from brisa.core.reactors._select import SelectReactor
    reactor = SelectReactor()

    from relayctrl.control import Controller
    controller = Controller(RELAY_DIR, relays)

    from relayctrl.upnp import RelayDevice

    device = RelayDevice(relays)
    device.start()
    reactor.add_after_stop_func(device.stop)
    reactor.main()

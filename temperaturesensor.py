import optparse
import brisa.core

from brisa.core.reactors._select import SelectReactor
import daemon

reactor = SelectReactor()

from temperature import oregon
from temperature import upnp


import os
import shelve

devices = []
relay = None
shelf = None
ems100 = None

def setpoint_achieved_changed(setpoint):
    print 'Setpoint achieved changed'
    active = 0
    for device in devices:
        if not device.setpoint.setpoint_achieved:
            active = 1
    if relay is not None:
        os.write(relay, 'CFH=%d\n' % active)


def _sensor_detected(sensor):
    print 'New sensor detected'
    device = upnp.TemperatureDevice(sensor)
    device.setpoint.register_setpoint_achieved(setpoint_achieved_changed)
    device.start()
    devices.append(device)
    setpoint_achieved_changed(device.setpoint)


def log_temperature():
    with open('/var/run/temperature', 'w') as f:
        for device in devices:
            n = device.name
            t = device.sensor.get_temperature()
            f.write('%s=%d' % (n, t))



def _after_stop():
    global devices, shelf, relay
    for device in devices:
        device.stop()
    devices = []
    if shelf:
        shelf.close()
        shelf = None

    if relay is not None:
        os.close(relay)
        relay = None


def init():
    global ems100,shelf,relay
    shelf = shelve.open('temperature.shelf', protocol=-1)
    upnp.shelf = shelf
    brisa.core.reactor.add_after_stop_func(_after_stop)
    ems100 = oregon.EMS100(_sensor_detected)
    relay = os.open('/var/run/relay/ctrl', os.O_RDWR | os.O_NONBLOCK)
    reactor.add_timer(60, log_temperature)

def run():
    try:
        reactor.main()
    except:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-d', '--daemon', action="store_true", dest="daemon", help="Start as a daemon")
    options,args = parser.parse_args()
    try:
        init()
        if options.daemon:
            with daemon.DaemonContext():
                run()
        else:
            run()

    except:
        import traceback
        traceback.print_exc()

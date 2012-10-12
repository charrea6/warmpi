import optparse
import uuid
import brisa.core

from brisa.core.reactors._select import SelectReactor
import daemon

reactor = SelectReactor()

from temperature import oregon
from temperature import upnp

from relayctrl.client import LocalClient

import os
import shelve

devices = []
thermostats = []
relay = None
shelf = None
ems100 = None

class Thermostat(object):
    def __init__(self, sensor):
        self.sensor = sensor
        self.name = sensor.name
        self.uuid = shelf.get(sensor.name + '\uuid', None)
        if self.uuid is None:
            self.uuid = 'uuid:%s' % uuid.uuid4()
            shelf[sensor.name + '\uuid'] = self.uuid
        self._zone = shelf.get(sensor.name + '\zone', '')
        self._setpoint = shelf.get(sensor.name + '\setpoint', 50.0)
        self._setpoint_achieved = False
        self.setpoint_achieved_listeners = []
        self.temperature_listeners = []
        sensor.add_temperature_changed(self.__temperature_changed)
        self.__check_setpoint()

    def register_temperature_listener(self, cb):
        self.temperature_listeners.append(cb)

    def register_setpoint_achieved_listener(self, cb):
        self.setpoint_achieved_listeners.append(cb)

    @property
    def temperature(self):
        return self.sensor.temperature

    def _get_zone(self):
        return self._zone

    def _set_zone(self, zone):
        self._zone = zone
        shelf[self.sensor.name + '\zone'] = zone

    zone = property(_get_zone, _set_zone)

    def _get_setpoint(self):
        return self._setpoint

    def _set_setpoint(self, setpoint):
       self._setpoint = setpoint
       shelf[self.sensor.name + '\setpoint'] = setpoint
       self.__check_setpoint()

    setpoint = property(_get_setpoint, _set_setpoint)

    @property
    def setpoint_achieved(self):
        return self._setpoint_achieved

    def __check_setpoint(self):
        orig_setpoint_achieved = self._setpoint_achieved
        self._setpoint_achieved = self.sensor.temperature >= self._setpoint
        if orig_setpoint_achieved != self._setpoint_achieved:
            for cb in self.setpoint_achieved_listeners:
                cb(self)

    def __temperature_changed(self, sensor, temp):
        for cb in self.temperature_listeners:
            cb(self, temp)
        self.__check_setpoint()
        

def setpoint_achieved_changed(setpoint):
    heating_required = 0
    for ts in thermostats:
        if not ts.setpoint_achieved:
            heating_required = 1
            break
    relay.set_state('CFH', heating_required)


def _sensor_detected(sensor):
    ts = Thermostat(sensor)
    thermostats.append(ts)
    device = upnp.TemperatureDevice(ts)
    ts.register_setpoint_achieved_listener(setpoint_achieved_changed)
    ts.register_temperature_listener(log_temperature)
    device.start()
    devices.append(device)
    setpoint_achieved_changed(None)
    log_temperature(None, None)


def log_temperature(sensor, temp):
    try:
        with open('/var/run/temperature', 'w') as f:
            for ts in thermostats:
                n = ts.name
                t = ts.temperature
                f.write('%s=%f\n' % (n, t))
    except:
        pass



def _after_stop():
    global devices, shelf, relay
    for device in devices:
        device.stop()
    devices = []
    if shelf:
        shelf.close()
        shelf = None

    if relay is not None:
        relay.close()
        relay = None


def init():
    global ems100,shelf,relay
    shelf = shelve.open('temperature.shelf', protocol=-1)
    brisa.core.reactor.add_after_stop_func(_after_stop)
    ems100 = oregon.EMS100(_sensor_detected)
    relay = LocalClient()
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

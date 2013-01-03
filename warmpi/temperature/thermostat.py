import uuid
import logging

class Thermostat(object):
    def __init__(self, sensor, shelf):
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
        self.shelf = shelf
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
        self.shelf[self.sensor.name + '\zone'] = zone
        self.shelf.sync()
        logging.info('Update zone for sensor %s, new zone %s', self.sensor.name, zone)

    zone = property(_get_zone, _set_zone)

    def _get_setpoint(self):
        return self._setpoint

    def _set_setpoint(self, setpoint):
        self._setpoint = setpoint
        self.shelf[self.sensor.name + '\setpoint'] = setpoint
        self.shelf.sync()
        logging.info('Update setpoint for sensor %s, new setpoint %f', self.sensor.name, setpoint)
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

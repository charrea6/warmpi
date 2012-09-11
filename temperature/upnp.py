import os
from socket import gethostname

from brisa.core import reactor
from brisa.upnp.device import Device
from brisa.upnp.device.service import Service

sensor_spcd = os.path.join(os.path.dirname(__file__), 'temperaturesensor_scpd.xml')
setpoint_spcd = os.path.join(os.path.dirname(__file__), 'temperaturesetpoint_scpd.xml')

class TemperatureSensor(Service):
    def __init__(self, sensor):
        super(TemperatureSensor, self).__init__('temp',
            'urn:schemas-upnp-org:service:TemperatureSensor:1',
            scpd_xml_filepath=sensor_spcd)
        self.sensor = sensor
        self.name = sensor.name
        self.application = 'Room'
        self.zone = shelf.get(sensor.name + '\zone', '')
        self.set_state_variable('Name', self.name)
        self.set_state_variable('Application', self.application)
        self.set_state_variable('CurrentTemperature', self.get_temperature())
        self.set_state_variable('X_Zone', self.zone)
        reactor.add_timer(10, self.monitor_temperature)

    def get_temperature(self):
        return int(self.sensor.temperature * 100)

    def soap_GetCurrentTemperature(self, *args, **kwargs):
        return {'CurrentTemp': self.get_temperature()}

    def soap_GetApplication(self, *args, **kwargs):
        return {'CurrentApplication': self.application}

    def soap_GetName(self, *args, **kwargs):
        return {'CurrentName': self.name}

    def soap_X_GetZone(self, *args, **kwargs):
        return {'CurrentZone': self.zone}

    def soap_X_SetZone(self, *args, **kwargs):
        self.zone = kwargs['NewZone']
        shelf[self.sensor.name + '\zone'] = self.zone
        self.set_state_variable('X_Zone', self.zone)
        return {}

    def monitor_temperature(self):
        t = self.get_temperature()
        self.set_state_variable('CurrentTemperature', t)
        return True


class TemperatureSetpoint(Service):
    def __init__(self, sensor):
        super(TemperatureSetpoint, self).__init__('tempsetpoint',
            'urn:schemas-upnp-org:service:TemperatureSetpoint:1',
            scpd_xml_filepath=setpoint_spcd)
        self.sensor = sensor
        sensor.add_temperature_changed(self.__tempurature_changed)
        self.setpoint = shelf.get(sensor.name + '\setpoint', 5000) # Start off at max so we don't switch on the
        self.setpoint_achieved = False
        self.setpoint_achieved_cbs = []
        self.check_setpoint()

    def soap_GetApplication(self, *args, **kwargs):
        return {'CurrentApplication':'Heating'}

    def soap_SetCurrentSetpoint(self, *args, **kwargs):
        self.setpoint = int(kwargs['NewCurrentSetpoint'])
        shelf[self.sensor.name + '\setpoint'] = self.setpoint
        self.check_setpoint()
        return {}

    def soap_GetCurrentSetpoint(self, *args, **kwargs):
        return {'CurrentSP':self.setpoint}

    def soap_GetSetpointAchieved(self, *args, **kwargs):
        return {'CurrentSPA':self.setpoint_achieved}

    def soap_GetName(self, *args, **kwargs):
        return {'CurrentName':self.sensor.name}

    def __tempurature_changed(self, sensor, temp):
        self.check_setpoint()

    def check_setpoint(self):
        orig_setpoint_achieved = self.setpoint_achieved
        self.setpoint_achieved = (self.sensor.temperature * 100) >= self.setpoint
        if orig_setpoint_achieved != self.setpoint_achieved:
            self.set_state_variable('SetpointAchieved', int(self.setpoint_achieved))
            for cb in self.setpoint_achieved_cbs:
                cb(self)

    def register_setpoint_achieved(self, cb):
        self.setpoint_achieved_cbs.append(cb)


class TemperatureDevice(Device):
    def __init__(self, sensor):
        name = sensor.name
        uuid = shelf.get(name + '\uuid', None)
        if uuid is None:
            import uuid
            uuid = 'uuid:%s' % uuid.uuid4()
            shelf[name + '\uuid'] = uuid
        super(TemperatureDevice,self).__init__('urn:schemas-home-lan:device:TemperatureMonitor:1',
            gethostname() + ' : ' + name, udn=uuid)
        self.sensor = TemperatureSensor(sensor)
        self.setpoint = TemperatureSetpoint(sensor)
        self += self.sensor
        self += self.setpoint


shelf = {}

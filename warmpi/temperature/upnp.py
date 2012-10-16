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
        self.application = 'Room'
        self.set_state_variable('Name', self.sensor.name)
        self.set_state_variable('Application', self.application)
        self.set_state_variable('CurrentTemperature', self.get_temperature())
        self.set_state_variable('X_Zone', self.sensor.zone)
        sensor.register_temperature_listener(self.__temperature_changed)

    def get_temperature(self):
        return int(self.sensor.temperature * 100)

    def soap_GetCurrentTemperature(self, *args, **kwargs):
        return {'CurrentTemp': self.get_temperature()}

    def soap_GetApplication(self, *args, **kwargs):
        return {'CurrentApplication': self.application}

    def soap_GetName(self, *args, **kwargs):
        return {'CurrentName': self.sensor.name}

    def soap_X_GetZone(self, *args, **kwargs):
        return {'CurrentZone': self.sensor.zone}

    def soap_X_SetZone(self, *args, **kwargs):
        self.sensor.zone = kwargs['NewZone']
        self.set_state_variable('X_Zone', self.sensor.zone)
        return {}

    def __temperature_changed(self, sensor, temp):
        t = self.get_temperature()
        self.set_state_variable('CurrentTemperature', t)


class TemperatureSetpoint(Service):
    def __init__(self, sensor):
        super(TemperatureSetpoint, self).__init__('tempsetpoint',
            'urn:schemas-upnp-org:service:TemperatureSetpoint:1',
            scpd_xml_filepath=setpoint_spcd)
        self.sensor = sensor
        sensor.register_setpoint_achieved_listener(self.__setpoint_achieved_changed)

    def soap_GetApplication(self, *args, **kwargs):
        return {'CurrentApplication':'Heating'}

    def soap_SetCurrentSetpoint(self, *args, **kwargs):
        self.sensor.setpoint = int(kwargs['NewCurrentSetpoint']) / 100.0
        return {}

    def soap_GetCurrentSetpoint(self, *args, **kwargs):
        return {'CurrentSP':int(self.sensor.setpoint * 100)}

    def soap_GetSetpointAchieved(self, *args, **kwargs):
        return {'CurrentSPA':int(self.sensor.setpoint_achieved)}

    def soap_GetName(self, *args, **kwargs):
        return {'CurrentName':self.sensor.name}

    def __setpoint_achieved_changed(self, sensor):
        self.set_state_variable('SetpointAchieved', int(self.sensor.setpoint_achieved))


class TemperatureDevice(Device):
    def __init__(self, sensor):
        super(TemperatureDevice,self).__init__('urn:schemas-home-lan:device:TemperatureMonitor:1',
            gethostname() + ' : ' + sensor.name, udn=sensor.uuid)
        self.sensor = TemperatureSensor(sensor)
        self.setpoint = TemperatureSetpoint(sensor)
        self += self.sensor
        self += self.setpoint

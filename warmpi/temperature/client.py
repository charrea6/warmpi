import warmpi

class LocalClient(object):
    def __init__(self):
        self.client = warmpi.get_client('temperature')
    
    def get_temperatures(self):
        return self.client.call('get_temperatures')
        
    def get_thermostats(self):
        return self.client.call('get_thermostats')
        
    def get_thermostat_temperature(self, thermostat):
        return self.client.call('get_thermostat_temperature', thermostat)
        
    def set_thermostat_name(self, thermostat, name):
        self.client.call('set_thermostat_name', thermostat, name)
    
    def get_thermostat_name(self, thermostat):
        return self.client.call('get_thermostat_name', thermostat)
    
    def set_thermostat_zone(self, thermostat, zone):
        self.client.call('set_thermostat_zone', thermostat, zone)
    
    def get_thermostat_zone(self, thermostat):
        return self.client.call('get_thermostat_zone', thermostat)

    def set_thermostat_setpoint(self, thermostat, setpoint):
        self.client.call('set_thermostat_setpoint', thermostat, setpoint)
    
    def get_thermostat_setpoint(self, thermostat):
        return self.client.call('get_thermostat_setpoint', thermostat)

    def set_zone_setpoint(self, zone, setpoint):
        self.client.call('set_zone_setpoint', zone, setpoint)


import cherrypy

from warmpi.web import no_cache
from warmpi.temperature.client import LocalClient

class Thermostat(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @no_cache
    def index(self):
        c = LocalClient()

        if cherrypy.request.method == 'POST':
            c.set_zone_setpoint(cherrypy.request.json['zone'], cherrypy.request.json['setpoint'])

        thermostats = {}
        for name,(zone, temperature, setpoint) in  c.get_thermostats().items():
            thermostats[name] = {'zone':zone, 'temperature': temperature, 'setpoint':setpoint}

        return thermostats

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @no_cache
    def default(self, *args):
        if len(args) >= 1:
            thermostat = args[0]

            if len(args) == 1:
                if cherrypy.request.method == 'GET':
                    return thermostat
                raise cherrypy.HTTPError(403)

            elif len(args) == 2:
                handler = getattr(self, 'thermostat_' + args[1], None)
                if handler is not None:
                    return handler(thermostat)

        raise cherrypy.NotFound()

    def thermostat_zone(self, thermostat):
        c = LocalClient()
        if cherrypy.request.method == 'GET':
            zone = c.get_thermostat_zone(thermostat)
            return {'zone':zone}
        elif cherrypy.request.method == 'POST':
            zone = cherrypy.request.json['zone']
            c.set_thermostat_zone(thermostat, zone)
            return {'zone':zone}
        raise cherrypy.HTTPError(403)

    def thermostat_temperature(self, thermostat):
        c = LocalClient()
        if cherrypy.request.method == 'GET':
            return {'temperature':c.get_thermostat_temperature(thermostat)}
        raise cherrypy.HTTPError(403)

    def thermostat_setpoint(self, thermostat):
        c = LocalClient()
        if cherrypy.request.method == 'GET':
            return {'setpoint':c.get_thermostat_setpoint(thermostat)}

        elif cherrypy.request.method == 'POST':
            sp = cherrypy.request.json['setpoint']
            c.set_thermostat_setpoint(thermostat, sp)
            return {'setpoint':sp}
        raise cherrypy.HTTPError(403)

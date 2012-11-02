import os
import datetime

import cherrypy

from warmpi.web.api.relay import Relay
from warmpi.web.api.thermostat import Thermostat
from warmpi.web.api.schedule import Schedule

class WebAPI(object):
    def __init__(self):
        self.relay = Relay()
        self.thermostat = Thermostat()
        self.schedule = Schedule()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def info(self):
        with open('/proc/uptime') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = str(datetime.timedelta(seconds = uptime_seconds))
        return {'uptime':uptime_string, 'load_average':os.getloadavg(), 'datetime':datetime.datetime.now().ctime()}

    @cherrypy.expose
    def index(self):
        return "This path is used for the JSON API"
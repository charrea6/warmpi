import cherrypy

from warmpi.relayctrl.client import LocalClient

class Relay(object):
    relays = ('HW', 'CH', 'CFH')

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        c = LocalClient()
        states = {}
        for r in self.relays:
            states[r] = c.get_state(r)
        return states

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def default(self, relay):
        if relay not in self.relays:
            raise cherrypy.NotFound()
        c = LocalClient()
        if cherrypy.request.method == 'POST':
            c.set_state(relay, bool(cherrypy.request.json['active']))
        return {'active': c.get_state(relay)}

import cherrypy

from warmpi.web import no_cache
from warmpi.schedule.client import LocalClient

class Schedule(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @no_cache
    def index(self):
        c = LocalClient()
        program = c.get_active_program()
        periods = [ {'start':p.start.strftime('%H:%m'), 'end':p.end.strftime('%H:%M'), 'system':p.system} for p in c.get_active_periods()]
        return {'active_program':program.name, 'active_program_id': program.id, 'active_periods':periods}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @no_cache
    def default(self, *args):
        return ()

class Program(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @no_cache
    def index(self):
        c = LocalClient()
        progs = c.get_programs()
        return {'programs':[{'name':p.name, 'id':p.id, 'active':p.active} for p in progs]}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @no_cache
    def active(self):
        c = LocalClient()

        if cherrypy.request.method == 'POST':
            LocalClient().set_active_program(cherrypy.request.json['id'])

        program = c.get_active_program()
        return {'name': program.name, 'id':program.id}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @no_cache
    def default(self, *args):
        return ()

class Period(object):
    def index(self):
        pass

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @no_cache
    def default(self, *args):
        c = LocalClient()

        if len(args) == 1:
            c.get_period(args[0])
            return

        elif len(args) == 2:
            pass

        return ()
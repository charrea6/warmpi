import cherrypy


class Schedule(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        return {'active_program':'Winter', 'active_periods':[
            {'start':'17:00', 'end':'23:00', 'system':'CH'},
            {'start':'17:00', 'end':'21:00', 'system':'HW'}
        ]}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def default(self, *args):
        return ()
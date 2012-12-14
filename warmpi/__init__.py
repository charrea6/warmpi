import os
import pwd
import optparse
import shelve
import logging

import daemon

LOG_PATH = '/var/log/warmpi'
BASE_PATH = '/var/run/warmpi'

class PIDFile(object):
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        with open(self.filename, 'w') as f:
            f.write('%d\n' % os.getpid())

    def __exit__(self, exc_type, exc_value, traceback):
        os.remove(self.filename)
        
class SubSystem(object):
    def __init__(self, name, user, daemonize):
        self.name = name
        self.dir = os.path.join(BASE_PATH, name)
        self.server = None
        self._shelf = None
        self.daemon = None
        if daemonize:
            out = file(os.path.join(LOG_PATH, '%s.stdout.log' % name), 'w')
            err = file(os.path.join(LOG_PATH, '%s.stderr.log' % name), 'w')
            self.daemon = daemon.DaemonContext(working_directory=self.dir,
                                 stdout=out,
                                 stderr=err,              
                                 pidfile=PIDFile(os.path.join(self.dir, '%s.pid' % name)))
            self.daemon.open()

        # Create run directory
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        os.chdir(self.dir)

        # Initialise logging
        if not os.path.exists(LOG_PATH):
            os.makedirs(LOG_PATH)
        logging.basicConfig(filename=os.path.join(LOG_PATH, '%s.log' % name), 
                            level=logging.DEBUG,
                            format="%(asctime)s - %(levelname)s - %(message)s")

        # Only log error messages from brisa
        logging.getLogger('RootLogger').setLevel(logging.ERROR)
        logging.getLogger('core').setLevel(logging.ERROR)
        logging.getLogger('upnp').setLevel(logging.ERROR)

        # Perform subclass initialisation while we still have some privileges.
        self.privileged_init()

        if os.getuid() == 0:
            p = pwd.getpwnam(user)
            os.chown(self.dir, p.pw_uid, p.pw_gid)

            # Drop privileges
            os.setgid(p.pw_gid)
            os.setuid(p.pw_uid)
            os.environ['USER'] = user
            os.environ['HOME'] = self.dir

        from brisa.core.reactors._select import SelectReactor
        self.reactor = SelectReactor()
        self.reactor.add_after_stop_func(self.after_stop)

    def privileged_init(self):
        pass

    @property
    def shelf(self):
        if self._shelf is None:
            self._shelf = shelve.open(os.path.join(self.dir, 'shelf'), protocol=-1)
        return self._shelf

    def create_server(self, funcs):
        if self.server is None:
            from warmpi.ipc import IPCServer

            self.server = IPCServer(self.dir, funcs)
        else:
            self.server.funcs = funcs

    def run(self):
        try:
            self.reactor.main()
        except:
            logging.error('Exception in run', exc_info=True)


    def after_stop(self):
        if self._shelf is not None:
            self._shelf.close()

        if self.daemon is not None:
            self.daemon.close()



def get_optparse():
    parser = optparse.OptionParser()
    parser.add_option('-d', '--daemon', action="store_true", dest="daemon", help="Start as a daemon")
    parser.add_option('-u', '--user', dest="user", default="warmpi",
        help="User to switch to after acquiring resources.")
    return parser


def get_client(name):
    dir = os.path.join(BASE_PATH, name)
    from warmpi.ipc import IPCClient
    return IPCClient(dir)

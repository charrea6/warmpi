import os

import brisa.core
from brisa.core.ireactor import EVENT_TYPE_READ

class Controller(object):
    def __init__(self, path, relays):
        self.state_path = os.path.join(path, 'state')
        self.relays = relays
        for relay in relays.values():
            relay.register_update(self.relay_updated)

        control_path = os.path.join(path, 'ctrl')
        # Create control fifo
        if not os.path.exists(control_path):
            try:
                os.mkfifo(control_path)
            except:
                pass
        os.chmod(control_path, 0666)
        self.fifo = open(control_path, 'r+')

        brisa.core.reactor.add_fd(self.fifo, self.__fifo_read, EVENT_TYPE_READ)

        # Create state file
        self.__write_state()


    def relay_updated(self, relay):
        self.__write_state()


    def __fifo_read(self, fd, event):
        try:
            b = self.fifo.readline().strip()
            relay, value = b.split('=')
            if value == '0' or value.lower() == 'false':
                value = False
            elif value == '1' or value.lower() == 'true':
                value = True
            else:
                raise ValueError('Invalid state value %r' % value)
            self.relays[relay].set_active(value)
        except:
            import traceback
            traceback.print_exc()
        return True


    def __write_state(self):
        try:
            with open(self.state_path, 'w') as f:
                for relay,value in self.relays.items():
                    f.write('%s=%d\n' % (relay, value.state))
        except:
            print 'Failed to write state file'

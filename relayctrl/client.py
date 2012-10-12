import os


class LocalClient(object):
    def __init__(self):
        self.fifo = os.open('/var/run/relay/ctrl', os.O_RDWR | os.O_NONBLOCK)

    def close(self):
        os.close(self.fifo)

    def set_state(self, relay, on):
        if on:
            v = 1
        else:
            v = 0
        os.write(self.fifo, '%s=%d\n' % (relay,v))

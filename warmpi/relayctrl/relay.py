
from warmpi.relayctrl import gpio

class Relay(object):
    def __init__(self, pin):
        self.state = False
        self.update_cbs = []
        self.channel = gpio.channel(pin, gpio.OUT, gpio.BCM)
        self.set_active(False)

    def register_update(self, cb):
        self.update_cbs.append(cb)

    def set_active(self, active):
        self.state = active
        self.channel.output(not active)
        if self.update_cbs:
            for cb in self.update_cbs:
                cb(self)

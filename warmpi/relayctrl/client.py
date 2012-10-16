import warmpi

class LocalClient(object):
    def __init__(self):
        self.client = warmpi.get_client('relay')

    def set_state(self, relay, on):
        return self.client.call('set_state', relay, on)

    def get_state(self, relay):
        return self.client.call('get_state', relay)

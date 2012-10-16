from socket import gethostname

from brisa.upnp.device import Device
from brisa.upnp.device.service import Service, ErrorCode

import os.path

spcd_path = os.path.join(os.path.dirname(__file__),'relaycontroller_scpd.xml')

class RelayController(Service):
    def __init__(self, relays):
        super(RelayController, self).__init__('relay',
            'urn:schemas-home-lan:device:RelayContoller:1',
            scpd_xml_filepath=spcd_path)
        self.relays = relays

    def soap_GetRelayState(self, *args, **kwargs):
        return {'State': self.relays[kwargs['Relay']].state}


    def soap_SetRelayState(self, *args, **kwargs):
        value = kwargs['State']
        if value == '0' or value.lower() == 'false':
            value = False
        elif value == '1' or value.lower() == 'true':
            value = True
        else:
            raise ErrorCode(402)
        relay = self.relays[kwargs['Relay']]
        relay.set_active(value)
        return {}


class RelayDevice(Device):
    def __init__(self, relays):
        super(RelayDevice,self).__init__('urn:schemas-home-lan:device:RelayDevice:1', gethostname())
        self += RelayController(relays)

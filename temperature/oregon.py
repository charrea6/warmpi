# Inspiration for this taken from https://github.com/barnybug/wmr100/blob/master/wmr100.c#
# and wview wmrusbprocotol.c (http://www.wviewweather.com)

import hidapi
import threading

class OregonWeatherStation(object):
    VENDOR_ID=0x0fde
    PRODUCT_ID=0xca01
    INIT_PACKET = reduce(lambda a,b: a+chr(b), [0x00, 0x20, 0x00, 0x08, 0x01, 0x00, 0x00, 0x00, 0x00], '')
    READY_PACKET = reduce(lambda a,b: a+chr(b), [0x00, 0x01, 0xd0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], '')
    PACKET_LENGTHS = { 0x41:17, 0x42:12, 0x44:7, 0x46:8, 0x47:5, 0x48:11, 0x60:12}

    def __init__(self, temperature_updated):
        self.device = hidapi.Device(self.VENDOR_ID, self.PRODUCT_ID)
        self.temperature_updated = temperature_updated
        self.init()

    def init(self):
        self.buffer = []
        self.device.write(self.INIT_PACKET)
        self.device.write(self.READY_PACKET)

    def __read_byte(self):
        while not self.buffer:
            data = self.device.read(8)
            pkt_len = ord(data[0])
            self.buffer = [ord(b) for b in data[1:1 + pkt_len]]
        return self.buffer.pop(0)

    def __verify_checksum(self, data):
        result = 0
        l = len(data)
        checksum = data[l - 2] + (data[l - 1] << 8)
        for b in data[:-2]:
            result += b
        return checksum == result

    def process_temperature(self, data):
        sensor = data[2] & 0x0f
        temp = (data[3] + ((data[4] & 0x0f) << 8)) / 10.0;
        if ((data[4] >> 4) == 0x8):
            temp = -temp
        self.temperature_updated(sensor, temp)

    def read_data(self):
        ff_found = False
        while True:
            i = self.__read_byte()
            if i == 0xff:
                if ff_found:
                    break
                else:
                    ff_found = True
        i = self.__read_byte()
        type = self.__read_byte()
        data_len = self.PACKET_LENGTHS.get(type, 0) - 2
        data = [i, type]
        while data_len:
            data.append(self.__read_byte())
            data_len -= 1

        if self.__verify_checksum(data) and type == 0x42:
            self.process_temperature(data)
        # Drop bad packets silently.
        self.device.write(self.READY_PACKET)

class EMS100Sensor(object):
    def __init__(self, name):
        self.name = name
        self.temperature = None
        self.temperature_changed = []

    def add_temperature_changed(self, cb):
        self.temperature_changed.append(cb)

    def set_temperature(self, temp):
        if self.temperature != temp:
            self.temperature = temp
            for cb in self.temperature_changed:
                cb(self, temp)


class EMS100(object):
    def __init__(self, sensor_detected):
        self.sensor_detected = sensor_detected
        self.sensors = {}
        self.device = OregonWeatherStation(self.__temperature_updated)
        self.processing_thread = threading.Thread(name='EMS100 Processing Thread', target=self.__process_data)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def __temperature_updated(self, sensor, temperature):
        if sensor not in self.sensors:
            if sensor == 0:
                name = 'Main'
            else:
                name = 'Remote %d' % sensor
            self.sensors[sensor] = EMS100Sensor(name)
            new_sensor = True
        else:
            new_sensor = False

        self.sensors[sensor].set_temperature(temperature)
        if new_sensor:
            if self.sensor_detected:
                self.sensor_detected(self.sensors[sensor])

    def __process_data(self):
        while True:
            self.device.read_data()

if __name__== '__main__':
    def temp_updated(sensor, temp):
        print '%d: %f' % (sensor, temp)

    station = OregonWeatherStation(temp_updated)
    while True:
        station.read_data()


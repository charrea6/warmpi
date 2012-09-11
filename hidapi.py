from ctypes import *
from ctypes.util import find_library

import sys

# ctypes wrapper around hidapi
class hid_device_info(Structure):
    pass

hid_device_info_p = POINTER(hid_device_info)
hid_device_info._fields_ = [('path', c_char_p),
                            ('vendor_id', c_ushort),
                            ('product_id', c_ushort),
                            ('serial_number', c_wchar_p),
                            ('release_number', c_ushort),
                            ('manufacturer_string', c_wchar_p),
                            ('product_string', c_wchar_p),
                            ('usage_page', c_ushort),
                            ('usage', c_ushort),
                            ('interface_number', c_int),
                            ('next', hid_device_info_p)]

hid_device = c_void_p

class Interface(object):
    def __init__(self, lib):
        funcs = (['hid_init', [], c_int],
                 ['hid_exit', [], c_int],
                 ['hid_enumerate', [c_ushort,c_ushort], hid_device_info_p],
                 ['hid_free_enumeration', [hid_device_info_p], None],
                 ['hid_open', [c_ushort,c_ushort, c_wchar_p], hid_device],
                 ['hid_open_path', [c_char_p], hid_device],
                 ['hid_write', [hid_device, c_char_p, c_uint], c_int],
                 ['hid_read_timeout', [hid_device, c_char_p, c_uint, c_int],  c_int],
                 ['hid_read', [hid_device, c_char_p, c_uint],  c_int],
                 ['hid_set_nonblocking', [hid_device, c_int],  c_int],
                 ['hid_send_feature_report', [hid_device, c_char_p, c_uint],  c_int],
                 ['hid_get_feature_report', [hid_device, c_char_p, c_uint],  c_int],
                 ['hid_close', [hid_device],  None],
                 ['hid_get_manufacturer_string', [hid_device, c_wchar_p, c_uint],  c_int],
                 ['hid_get_product_string', [hid_device, c_wchar_p, c_uint],  c_int],
                 ['hid_get_serial_number_string', [hid_device, c_wchar_p, c_uint],  c_int],
                 ['hid_get_indexed_string', [hid_device, c_int, c_wchar_p, c_uint],  c_int],
                 ['hid_error', [hid_device],  c_wchar_p])

        for name,args,restype in funcs:
            func = getattr(lib, name)
            func.args = args
            func.restype = restype
            setattr(self, name, func)

# Python wrapper around ctype exposed API

class HIDException(Exception):
    pass

class DeviceInformation(object):
    """Object describing a HID device"""

    def __init__(self, dev_info):
        self.path = str(dev_info.path)
        self.vendor_id = dev_info.vendor_id
        self.product_id = dev_info.product_id
        self.serial_number = unicode(dev_info.serial_number)
        self.release_number = dev_info.release_number
        self.manufacturer_string = unicode(dev_info.manufacturer_string)
        self.product_string = unicode(dev_info.product_string)
        self.usage_page = dev_info.usage_page
        self.usage = dev_info.usage
        self.interface_number = dev_info.interface_number

def enumerate(vendor_id=0, product_id=0):
    """Enumerate the HID Devices.

    This function returns an iterator that iterates over all the HID devices
    attached to the system which match vendor_id and product_id. If vendor_id
    and product_id are both set to 0, then all HID devices will be returned.
    """
    r = _hidapi.hid_enumerate(vendor_id, product_id)
    if r is None:
        raise HIDException('Failed to enumerate devices')
    try:
        d = r
        while d:
            yield DeviceInformation(d.contents)
            d = d.contents.next
    finally:
        _hidapi.hid_free_enumeration(r)


class Device(object):
    def __init__(self, vendor_id=None, product_id=None, serial_number=None, path=None):
        """
        Opens a HID Device using either vendor_id/product_id or path.

        If path is not None then the device will attempt to be opened using the path.
        If vendor_id and product_id are defined an optional serial_number can also be specified.
        """
        if path is None:
            assert(vendor_id is not None and product_id is not None)
            self.device = _hidapi.hid_open(vendor_id, product_id, serial_number)
        else:
            self.device = _hidapi.hid_open_path(path)

        if self.device is None:
            raise HIDException('Failed to open device')

    def __del__(self):
        if self.device:
            _hidapi.hid_close(self.device)

    def __raise_or_return(self, r):
        if r == -1:
            raise HIDException(_hidapi.hid_error(self.device))
        return r

    def read(self, length, timeout=None):
        b = create_string_buffer(length + 1) # Additional byte for the Report number
        if timeout is None:
            self.__raise_or_return(_hidapi.hid_read(self.device, b, length))
        else:
            self.__raise_or_return(_hidapi.hid_read_timeout(self.device, b, length, timeout))
        r = ''
        for i in xrange(0, len(b)):
            r += b[i]
        return r

    def write(self, data):
        return self.__raise_or_return(_hidapi.hid_write(self.device, data, len(data)))

    def set_nonblocking(self, nonblocking):
        self.__raise_or_return(_hidapi.hid_set_non_blocking(self.device, nonblocking))

    def send_feature_report(self, data):
        return self.__raise_or_return(_hidapi.hid_send_feature_report(self.device, data, len(data) - 1))

    def get_feature_report(self, report_id, max_bytes=64):
        b = create_string_buffer(max_bytes) # Additional byte for the Report number
        b[0] = chr(report_id)
        self.__raise_or_return(_hidapi.hid_get_feature_report(self.device, b, max_bytes))
        return str(b)

    @property
    def manufacturer_string(self):
        b = create_unicode_buffer(255)
        self.__raise_or_return(_hidapi.hid_get_manufacturer_string(self.device, b, 255))
        return b.value

    @property
    def product_string(self):
        b = create_unicode_buffer(255)
        self.__raise_or_return(_hidapi.hid_get_product_string(self.device, b, 255))
        return b.value

    @property
    def serial_number(self):
        b = create_unicode_buffer(255)
        self.__raise_or_return(_hidapi.hid_get_serial_number_string(self.device, b, 255))
        return b.value

    def get_indexed_string(self, idx):
        b = create_unicode_buffer(255)
        self.__raise_or_return(_hidapi.hid_get_indexed_string(self.device, idx, b, 255))
        return b.value


path = find_library('hidapi-libusb')
if not path:
    if sys.platform == 'win32':
        path = 'hidapi.dll'
    else:
        path = './libhidapi-libusb.so'

if path:
    _hidapi = Interface(CDLL(path))
else:
    raise ImportError('Failed to find hidapi library')

_hidapi.hid_init()

import atexit
atexit.register(_hidapi.hid_exit)

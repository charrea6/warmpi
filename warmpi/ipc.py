import os
try:
    import cPickle as pickle
except:
    import pickle
import socket
import struct
import stat
import sys
import traceback

from brisa.core.ireactor import EVENT_TYPE_READ, EVENT_TYPE_EXCEPTION

class IPCServer(object):
    def __init__(self, path, funcs):
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ctrl_path = os.path.join(path, 'ctrl')
        if os.path.exists(ctrl_path):
            os.unlink(ctrl_path)
        self.server.bind(ctrl_path)
        self.server.listen(1)
        os.chmod(ctrl_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        self.clients = {}
        self.funcs = funcs

        from brisa.core import reactor
        reactor.add_fd(self.server.fileno(), self.__accept, EVENT_TYPE_READ)
 

    def __accept(self, fd, evt):
        client, _ = self.server.accept()
        from brisa.core import reactor
        reactor.add_fd(client.fileno(), self.__read, EVENT_TYPE_READ | EVENT_TYPE_EXCEPTION)
        self.clients[client.fileno()] = IPCConnection(client)
        return True

    def __read(self, fd, evt):
        remove = False
        if evt == EVENT_TYPE_EXCEPTION:
            remove = True
        elif evt == EVENT_TYPE_READ:
            code,data = None, None
            conn = self.clients[fd]
            try:
                code, data = conn.recv()
            except:
                remove = True

            if code == 'CALL':
                func,args,kwargs = data
                try:
                    r = self.funcs[func](*args, **kwargs)
                    resp = ('RET', r)
                except:
                    _,value,tb = sys.exc_info()
                    stack = traceback.extract_tb(tb)
                    resp = ('EXC', (value, stack))

                try:
                    conn.send(*resp)
                except:
                    remove = True

        if remove:
            del self.clients[fd]
        return not remove

class IPCClient(object):
    def __init__(self, path):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(os.path.join(path, 'ctrl'))
        self.conn = IPCConnection(sock)

    def call(self, func, *args, **kwargs):
        self.conn.send('CALL', (func, args, kwargs))
        code,data = self.conn.recv()
        if code == 'EXC':
            raise data[0]
        return data

class IPCConnection(object):
    def __init__(self, sock):
        self.sock = sock

    def recv(self):
        pkt_len, = struct.unpack('I', self.sock.recv(4))
        pkt_data = self.sock.recv(pkt_len)
        r = pickle.loads(pkt_data)
        return r 

    def send(self, code, data):
        pkt = pickle.dumps((code, data), -1)
        pkt_len = struct.pack('I', len(pkt))
        self.sock.send(pkt_len + pkt)

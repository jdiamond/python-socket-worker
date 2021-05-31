import socket
import time


SLEEP_BEFORE_RECONNECT = 1
RECEIVE_BUFFER_SIZE = 1024
TEXT_ENCODING = "ascii"


class Client:
    def __init__(self):
        self.state = None
        self.address = None
        self.socket = None
        self.buffer = ""
        self.on_connect = None
        self.on_message = None
        self.set_state("not_connected")

    def set_state(self, new_state):
        print("client changing state from {} to {}".format(self.state, new_state))
        self.state = new_state

    def connect(self, address):
        self.address = address
        while True:
            self.set_state("connecting")
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(self.address)
            except:
                self.set_state("connect_failed")
                time.sleep(SLEEP_BEFORE_RECONNECT)
            else:
                self.set_state("connected")
                if self.on_connect:
                    self.on_connect(self)
                break

    def send(self, message):
        self.socket.sendall((message + "\n").encode(TEXT_ENCODING))

    def loop_forever(self):
        while True:
            data = self.socket.recv(RECEIVE_BUFFER_SIZE)
            if not data:
                self.set_state("connection_closed")
                time.sleep(SLEEP_BEFORE_RECONNECT)
                self.connect(self.address)
                self.buffer = ""
                continue
            self.buffer = self.buffer + data.decode(TEXT_ENCODING)
            index = self.buffer.find("\n")
            while index != -1:
                message = self.buffer[:index]
                self.buffer = self.buffer[index + 1 :]
                if self.on_message:
                    self.on_message(self, message)
                index = self.buffer.find("\n")

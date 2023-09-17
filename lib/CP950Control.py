#!/usr/bin/env python3
#This class deals with communicating with the CP850 and CP950

import CP850Control

ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

PORT = 10001

class CP950Control(CP850Control.CP850Control):
    def __init__(self, host):
        super().__init__(host)

    def send(self, command):
        if self.socket is None:
            self.connect()
            if self.socket is None:
                return self.getState()
        try:
            self.socket.send(command.encode('UTF-8') + b"\r\n")
            result = self.socket.recv().decode('UTF-8').strip()
            return result
        except Exception as e:
            return "Error: " + str(e)

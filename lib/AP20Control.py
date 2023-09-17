#!/usr/bin/env python3
#This class deals with communicating with the AP20 and AP25

import board
import busio
import digitalio
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
import time
import Config

ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

# Datasat defined port.
PORT = 14500

class AP20Control(CinemaProcessor.CinemaProcessor):
    def __init__(self, host):
        super().__init__(host, PORT)

    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            result = self.send('@SYSTEM')
            if not result or result.startswith(ERROR_PREFIX):
                self.disconnect()
                return result
            return "connected"

    def connect(self):
        if self.socket is not None:
            self.disconnect()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.destination, self.port))
            s.settimeout(500)
            self.socket = s
        except Exception as e:
            print("Error: " + str(e))
            return "Error: " + str(e)
        return self.getState()

    def disconnect(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except  Exception as e:
                # LOGGER.exception("Failed to close connection")
                return "Error: " + str(e)
            finally:
                self.socket = None
        return self.getState()

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


    def getfader(self):
        returnFader = self.send('@FADER')
        # ~ print(returnFader)
        return self.stripvalue(returnFader)

    def setfader(self, value):
        return self.stripvalue(self.send(f'@FADER {value}'))

    def setmute(self, mute=1):
        return self.stripvalue(self.send(f'@MUTE {mute}'))

    def getmute(self):
        return self.stripvalue(self.send('@MUTE'))


    def displayfader(self):
        fader = self.getfader()
        if(isinstance(fader, int)):
            rawfader = str(fader)
            formattedfader = rawfader[:-1]+'.'+rawfader[-1:] #add decimal point one space over from the right
            return f' {str(formattedfader)}'
        else:
            return False


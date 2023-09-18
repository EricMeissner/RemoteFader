#!/usr/bin/env python3
#This class deals with communicating with the JSD60

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

PORT = 10001


class JSD60Control(CinemaProcessor.CinemaProcessor):
    def __init__(self, host):
        super().__init__(host, PORT)
        self.API_PREFIX='jsd60'

    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            result = self.send(f'{self.API_PREFIX}.sys.fader')
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

    # Extracts the actual value from the response from the Cinema processor
    # JSD60/100 just returns a value, not response text.
    def stripvalue(self, responseText):
        value = responseText
        if (value.isdigit()):
            return int(value)
        else:
            return value

    def addfader(self, value=1):
        #compensate for JSD faders having an extraneous trailing zero
        value=value*10
        currentFader = self.getfader()
        if(isinstance(value, int) and isinstance(currentFader, int)):
            newFader = currentFader + value
            if(newFader<0):
                self.setfader(0)
            elif(newFader>1000):
                self.setfader(1000)
            else:
                self.setfader(newFader)
            return True
        else:
            return False

    def getfader(self):
        returnFader = self.send(f'{self.API_PREFIX}.sys.fader')
        # ~ print(returnFader)
        return self.stripvalue(returnFader)

    def setfader(self, value):
        return self.stripvalue(self.send(f'{self.API_PREFIX}.sys.fader\t{value}'))

    def setmute(self, mute=1):
        return self.stripvalue(self.send(f'{self.API_PREFIX}.sys.fader\t{value}'))

    def getmute(self):
        return self.stripvalue(self.send(f'{self.API_PREFIX}.sys.mute'))

    def displayfader(self):
        fader = self.getfader()
        if(isinstance(fader, int)):
            rawfader = str(fader)
            formattedfader = rawfader[:-2]+'.'+rawfader[-2:-1] #add decimal point 2 spaces over from the right
            return f'{str(formattedfader)}'
        else:
            return False


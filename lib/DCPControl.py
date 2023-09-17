#Deals with communicating with the DCP line from QSC.

import board
import busio
import digitalio
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
import time
#import Config

ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

PORT = 4446

class DCPControl(CinemaProcessor.CinemaProcessor):
    def __init__(self, host, prefix):
        super().__init__(host, PORT)
        self.prefix = prefix
        #Prefixes include: "dcp100", "dcp200", "dcp300", and possibly "dpm100"

    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            result = self.send(f'{prefix}fader=')
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

    # Extracts the actual value from the response. Does not convert to number!
    def stripvalue(self, responseText):
        value = responseText.strip().split("=")[-1]
        return value

    # Adds or subtracts an integer to the fader
    # To match previous implementations, the integer is essentially divided by 10, so that 1 tic changes by 0.1dB
    def addfader(self, value=1):
        strValue = str(value)
        formattedValue = strValue[:-1]+'.'+strValue[-1:] #add decimal point one space over from the right
        if(value>=0):
            self.send(f'{prefix}fader=++{formattedValue}')
        else:
            self.send(f'{prefix}fader=-{formattedValue}')

    #Warning: Return
    def getfader(self):
        returnFader = self.send(f'{prefix}fader=')
        return  self.stripvalue(returnFader)

    #Warning: Returns strings
    def setfader(self, value):
        return  self.stripvalue(self.send(f'{prefix}fader={value}'))

    def setmute(self, mute=1):
        return  self.stripvalue(self.send(f'{prefix}mute={mute}'))

    def getmute(self):
        return  self.stripvalue(self.send(f'{prefix}mute='))

    def displayfader(self):
        fader = self.getfader()
        try:
            float(fader) #checks to see if the getfader result is a number, rather than an error message
            return  ' {fader}'
        except ValueError: #If getfader returns an error rather than a number, we this type error triggers to return False.
            return  False


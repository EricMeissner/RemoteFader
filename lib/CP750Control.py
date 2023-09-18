#!/usr/bin/env python3
#This class deals with communicating with the CP750

from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
#import time

ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

# Dolby defined port.
PORT = 61408
macrolist = ["dig_1", "dig_2", "dig_3", "dig_4", "analog", "non_sync", "mic"]

class CP750Control(CinemaProcessor.CinemaProcessor):
    def __init__(self, host):
        super().__init__(host, PORT)

    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            result = self.send('cp750.sys.fader ?')
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

    # Extracts the actual value from the response from the CP750
#     def stripvalue(self, responseText):
#         see CinemaProcessor

    # Adds or subtracts an integer to the fader
    def addfader(self, value=1):
        if(isinstance(value, int)):
            if(value>=0):
                self.send(f'cp750.ctrl.fader_delta +{value}')
            else:
                self.send(f'cp750.ctrl.fader_delta {value}')

    def getfader(self):
        returnFader = self.send('cp750.sys.fader ?')
        # ~ print(returnFader)
        return self.stripvalue(returnFader)

    def setfader(self, value):
        return self.stripvalue(self.send(f'cp750.sys.fader {value}'))

    def setmute(self, mute=1):
        return self.stripvalue(self.send(f'cp750.sys.mute {mute}'))

    def getmute(self):
        return self.stripvalue(self.send('cp750.sys.mute ?'))

    def getversion(self):
        return self.stripvalue(self.send('cp750.sysinfo.version ?'))


    def displayfader(self):
        fader = self.getfader()
        if(isinstance(fader, int)):
            rawfader = str(fader)
            formattedfader = rawfader[:-1]+'.'+rawfader[-1:] #add decimal point one space over from the right
            return f' {str(formattedfader)}'
        else:
            return False

    def setmacro(self, macro):
        if(macro.isdigit()):
            macro = int(macro)-1
            macrolist = self.getmacrolist()
            if (macro > -1 and  macro < len(macrolist)):
                macroname = self.getmacrolist()[macro]
                self.setmacrobyname(macroname)

    def setmacrobyname (self, macroname):
        return self.stripvalue(self.send(f'cp750.sys.input_mode {macroname}'))

    def getmacro(self):
        macroname = self.getmacroname()
        return self.getmacrolist().index(macroname)

    def getmacroname(self):
        return self.stripvalue(self.send('cp750.sys.input_mode ?'))

    def getmacrolist(self):
        return macrolist

#!/usr/bin/env python3
#This class deals with communicating with the Ovation

from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
#import time

ERROR_PREFIX='ERROR'
SOCKET_TIMEOUT=250

PORT = 44100
CLIENT_ID = "Fader"

class OvationControl(CinemaProcessor.CinemaProcessor):
    def __init__(self, host):
        super().__init__(host, PORT)
        self.macroList = []
        self.mute = 0
        self.dim = 0
        self.fader = None
        self.current_profile = 0

    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            result = self.send('get_current_preset')
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
            self.send(f'id {CLIENT_ID}')
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

    def updateState(self, rawResponse):

        # get mute
        index0 = rawResponse.find('MUTE ')
        if index0 > -1:
            index0 += 5
            indexF = rawResponse[index0:].find('\n')
            if indexF == -1:
                self.mute = int(rawResponse[index0:])
            else:
                self.mute = int(rawResponse[index0:(index0 + indexF)])

        # get dim
        index0 = rawResponse.find('DIM ')
        if index0 > -1:
            index0 += 4
            indexF = rawResponse[index0:].find('\n')
            if indexF == -1:
                self.dim = int(rawResponse[index0:])
            else:
                self.dim = int(rawResponse[index0:(index0 + indexF)])

        # get current preset
        index0 = rawResponse.find('CURRENT_PROFILE ')
        if index0 > -1:
            index0 += 15
            indexF = rawResponse[index0:].find('\n')
            if indexF == -1:
                self.current_profile = int(rawResponse[index0:])
            else:
                self.current_profile = int(rawResponse[index0:(index0 + indexF)])

        # get volume
        index0 = rawResponse.find('VOLUME ')
        if index0 > -1:
            index0 += 7
            indexF = rawResponse[index0:].find('\n')
            if indexF == -1:
                dbvolume = rawResponse[index0:]
            else:
                dbvolume = rawResponse[index0:(index0 + indexF)]
            # dbvolume = rawResponse[10:]
            # print(f'getFader: {dbvolume} dB')
            self.fader = self.dbtodolby(dbvolume)

        #get macroList if empty
        if len(self.macroList) ==0:
            profile = 0
            lastIndexF = 0
            while True:
                searchString = f'PROFILE {profile}: '
                index0 = rawResponse.find(searchString)
                if index0 > -1:
                    index0 += len(searchString)
                    indexF = rawResponse[index0:].find('\n')
                    if indexF == -1:
                        self.macroList.append(rawResponse[index0:])
                        #print(f'Profile {profile}: {self.macroList[profile]}')
                        break  # got to end of response
                    else:
                        self.macroList.append(rawResponse[index0:(index0 + indexF)])
                        lastIndexF = index0+indexF
                else:
                    if rawResponse[lastIndexF:].find('PROFILE ') > -1:
                        self.macroList.append('DISABLED')
                        if profile > 30:
                            print(f'Profile {profile}: {self.macroList[profile]}')
                            break
                    else:
                        break
                #print(f'Profile {profile}: {self.macroList[profile]}')
                profile += 1

    def send(self, command):
        # print(f'SENT: {command}')
        if self.socket is None:
            self.connect()
            if self.socket is None:
                return self.getState()
        try:
            self.socket.send(command.encode('UTF-8') + b"\n")
            result = self.socket.recv().decode('UTF-8').strip()
            # print(f'RESPONSE: {result}')
            self.updateState(result)
            return result
        except Exception as e:
            print("Error: " + str(e))
            return "Error: " + str(e)

    # def stripvalue(self, responseText):
    #     value = responseText.strip().split(" ")[1]
    #     return value

    # Adds or subtracts an integer to the fader
    def addfader(self, value=1):
        if(isinstance(value, int)):
            self.send(f'dvolume_0_10 {str(value/10)}')
        else:
            return False

    def getfader(self):
        if self.fader is None:
            self.send('dvolume_0_10 0')
        else:
            try:
                result = self.socket.recv().decode('UTF-8').strip()
                # print(f'RESPONSE: {result}')
                self.updateState(result)
            except Exception as e:
                print("Error: " + str(e))
                return False
        return self.fader

    def setfader(self, value):
        self.send(f'volume_0_10 {value}')

    def setmute(self, mute=1):
        self.send(f'mute {mute}')

    def togglemute(self):
        self.send('mute 2')

    def getmute(self):
        return self.mute

    def setdim(self, dim=1):
        self.send(f'dim {dim}')

    def toggledim(self):
        self.send('dim 2')

    def getdim(self):
        return self.dim

    def displayfader(self):
        return str(self.getfader())

    # Converts db to the ten point scale used by Dolby and JSD cinema processors
    def dbtodolby(self, dbVolume):
        try:
            dbVolume = float(dbVolume)
            if (dbVolume > 10):
                dbVolume = 10
            elif (dbVolume < -90):
                dbVolume = -90

            if (dbVolume > -10):
                dolby = (dbVolume / 3.33) + 7
            else:  # dbVolume <= -10
                dolby = (dbVolume / 20) + 4.5
            # round to nearest tenth.
            dolby = round(dolby * 10) / 10
            return str(dolby)
        except Exception as e:
            return False

    # set preset
    def setmacro(self, macro):
        macroID = int(macro)-1
        if macroID == -1:
            macroID = 9  # If someone presses the zero button, change it to select the 10th preset, id 9
        if macroID < len(self.macroList):
            if self.macroList[macroID] != "DISABLED":
                self.send(f'profile {macroID}')

    def setmacrobyname (self, macroname):
        if len(self.macroList) == 0:
            self.getmacrolist()
        if (macroname != "DISABLED"):
            macro = self.macroList.index(macroname)
            if macro != -1:
                self.setmacro(macro+1)
    #
    # get current preset number
    def getmacro(self):
        rawResponse = self.send("get_current_profile")
        return int(self.current_profile)+1


    def getmacroname(self):
        self.getmacro()
        if len(self.macroList):
            try:
                return self.macroList[int(self.current_profile)]
            except Exception as e:
                print("macro Error: " + str(e))
                i=0
                for macro in self.macroList:
                    print(f'profile {i}: {macro}')
                    i += 1
                return f'Profile {self.current_profile}'
        else:
            return "Profiles loading"

    def getmacrolist(self):
        return self.macroList



#!/usr/bin/env python3
#This class deals with communicating with Q-SYS.
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
#import time

ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

# Q-SYS defined port.
PORT = 1702

class QSYSControl(CinemaProcessor.CinemaProcessor):
    def __init__(self, host, faderName, muteName=None):
        super().__init__(host, PORT)
        self.faderName = faderName
        if muteName == "":
            self.muteName = None
        else:
            self.muteName = muteName

    def getState(self):
        if self.socket is None:
            return "disconnected"
        else:
            # Test if socket is alive...
            result = self.send('sg')
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
            except Exception as e:
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
        value = responseText.strip().split(" ")[-2]
        return value

    def addfader(self, value=1):
        currentFader = float(self.getfader())
        # print(f'current fader: {currentFader}')
        delfader = float(value) / 10.0
        # print(f'delfader: {delfader}')
        if (isinstance(delfader, float) and isinstance(currentFader, float)):
            newFader = currentFader + delfader
            # print(f'newFader: {newFader}')
            if (newFader < 0):
                self.setfader(0)
            elif (newFader > 100):
                self.setfader(10)
            else:
                self.setfader(newFader)
            return True
        else:
            return False


    def getfader(self):
        raw = self.send(f'cg "{self.faderName}"')
        dbfader = self.stripvalue(raw)
        dolbyfader = self.dbtodolby(dbfader)
        return dolbyfader

    # Warning: Returns string Uses Dolby 10-point system rather than db, value in 1/tenths
    def setfader(self, value):
        dbVolume = self.dolbytodb(value)
        dbfader = self.stripvalue(self.send(f'csv "{self.faderName}" {str(dbVolume)}'))
        dolbyfader = self.dbtodolby(dbfader)
        return dolbyfader

    def setmute(self, mute=1):
        if self.muteName is None:
            return 0
        mute = self.stripvalue(self.send(f'csv "{self.muteName}" {str(mute)}'))
        return int(mute)

    def getmute(self):
        if self.muteName is None:
            return 0
        mute = self.stripvalue(self.send(f'cg "{self.muteName}"'))
        return int(mute)

    def displayfader(self):
        fader = self.getfader()
        if (not fader):
            return False
        try:
            float(fader)  # checks to see if the getfader result is a number, rather than an error message
            return fader
        except ValueError:  # If getfader returns an error rather than a number, we this type error triggers to return False.
            return False

        # Converts the 0.0-10.0 scale used by the Dolby and JSD CPs to dB used by the DCP300

    def dolbytodb(self, dolbyVolume):
        dolbyVolume = float(dolbyVolume)
        if (dolbyVolume > 10):
            dolbyVolume = 10
        elif (dolbyVolume < 0):
            dolbyVolume = 0

        if (dolbyVolume > 4):
            db = 3.33 * (dolbyVolume - 7)
        else:  # dolbyVolume <=4
            db = 20 * (dolbyVolume - 4.5)
        # round to nearest tenth.
        db = round(db * 10) / 10
        return str(db)

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


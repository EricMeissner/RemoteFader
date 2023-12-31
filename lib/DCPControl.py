#Deals with communicating with the DCP line from QSC.

from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
import time

ERROR_PREFIX='Error'
ERROR_SUFFIX='invalid command'
SOCKET_TIMEOUT=250

PORT = 4446

class DCPControl(CinemaProcessor.CinemaProcessor):
    def __init__(self, host, prefix="dcp300"):
        super().__init__(host, PORT)
        self.prefix = prefix
        #Prefixes include: "dcp300" and possibly "dpm100"

    def getState(self):
        result = self.send('<?xml version="1.0"?><!--0000104--><GET_S RT="C00" ID="0" L1PW="qsc"><EGS O="0x001B0000" M="0"/></GET_S>')
        if not result or result.endswith(ERROR_SUFFIX) or result.startswith(ERROR_PREFIX):
            #print("GetState: disconnected")
            return "disconnected"
        else:
            #print("GetState: connected")
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
            print("Connect Error: " + str(e))
            return "Error: " + str(e)
        print("Connect Success!")
        return "connected"

    def disconnect(self):
        if self.socket is not None:
            try:
                self.socket.close()
            except  Exception as e:
                # LOGGER.exception("Failed to close connection")
                return "Error: " + str(e)
            finally:
                self.socket = None
        return "disconnected"

    def send(self, command):
        if self.socket is None:
            self.connect()
            if self.socket is None:
                return "Error: Socket is None"
        try:
            #print('Command: ' + command)
            self.socket.send(command.encode('UTF-8'))
            result = self.socket.recv().decode('UTF-8').strip()
            #print('Response: ' + result)
            return result
        except Exception as e:
            return "Error: " + str(e)

    # Extracts the actual value from the response. Does not convert to number!
    def stripvalue(self, responseText):
        value = responseText.strip().split("=")[-1]
        return value

    # Adds or subtracts an integer to the fader
    # value is in tenths of one point on the 10-point scale used by Dolby and the JSD line.
#    def addfader(self, value=1):
#        oldFader = float(self.getfader())
#        strValue = str(value)
#        formattedValue = strValue[:-1]+'.'+strValue[-1:] #add decimal point one space over from the right
#        self.send(f'<?xml version="1.0"?><!--0000{109+len(formattedValue)}--><SET_S RT="C00" ID="0" L1PW="qsc"><ESS O="0x00320000" M="0" F="{formattedValue}"/></SET_S>')

    def addfader(self, value=1):
        currentFader = float(self.getfader())
        #print(f'current fader: {currentFader}')
        delfader = float(value)/10.0
        #print(f'delfader: {delfader}')
        if(isinstance(delfader, float) and isinstance(currentFader, float)):
            newFader = currentFader + delfader
            #print(f'newFader: {newFader}')
            if(newFader<0):
                self.setfader(0)
            elif(newFader>100):
                self.setfader(10)
            else:
                self.setfader(newFader)
            return True
        else:
            return False

    #Warning: Returns string
    def getfader(self):
        rawResponse = self.send('<?xml version="1.0"?><!--0000104--><GET_S RT="C00" ID="0" L1PW="qsc"><EGS O="0x001B0000" M="0"/></GET_S>')
        if(not rawResponse or len(rawResponse) == 0):
            return False
        index0 = rawResponse.find(' F="')+4
        indexF = rawResponse[index0:].find('"')+index0
        dolbyfader = self.dbtodolby(rawResponse[index0:indexF])
        return dolbyfader

    #Warning: Returns string Uses Dolby 10-point system rather than db, value in 1/tenths
    def setfader(self, value):
        dbVolume = self.dolbytodb(value)
        #formattedValue = strValue[:-1]+'.'+strValue[-1:] #add decimal point one space over from the right
        rawResponse = self.send(f'<?xml version="1.0"?><!--0000{109+len(dbVolume)}--><SET_S RT="C00" ID="0" L1PW="qsc"><ESS O="0x001B0000" M="0" F="{dbVolume}"/></SET_S>')
        if(not rawResponse or len(rawResponse) == 0):
            return False
        index0 = rawResponse.find(' F="')+4
        #print(f'i0: {index0}')
        indexF = rawResponse[index0:].find('"')+index0
        #print(f'iF: {indexF}')
        dolbyVolume = self.dbtodolby(rawResponse[index0:indexF])
        return dolbyVolume

    def setmute(self, mute=1):
        if(mute):
            self.send('<?xml version="1.0"?><!--0000113--><SET_S RT="C00" ID="0" L1PW="qsc"><ESS O="0x001C0000" M="0" B="true"/></SET_S>')
        else:
            self.send('<?xml version="1.0"?><!--0000114--><SET_S RT="C00" ID="0" L1PW="qsc"><ESS O="0x001C0000" M="0" B="false"/></SET_S>')


    def getmute(self):
        rawResponse = self.send('<?xml version="1.0"?><!--0000104--><GET_S RT="C00" ID="0" L1PW="qsc"><EGS O="0x001C0000" M="0"/></GET_S>')
        if(not rawResponse or len(rawResponse) == 0):
            return False
        index0 = rawResponse.find(' B="')+4
        #print(f'i0: {index0}')
        indexF = rawResponse[index0:].find('"')+index0
        #print(f'iF: {indexF}')
        if (rawResponse[index0:indexF].lower() == "true"):
            return 1
        else:
            return 0

    def displayfader(self):
        fader = self.getfader()
        if(not fader):
            return False
        try:
            float(fader) #checks to see if the getfader result is a number, rather than an error message
            return  fader
        except ValueError: #If getfader returns an error rather than a number, we this type error triggers to return False.
            return  False


    # Converts the 0.0-10.0 scale used by the Dolby and JSD CPs to dB used by the DCP300
    def dolbytodb(self, dolbyVolume):
        dolbyVolume = float(dolbyVolume)
        if(dolbyVolume>10):
            dolbyVolume = 10
        elif(dolbyVolume<0):
            dolbyVolume = 0

        if (dolbyVolume>4):
            db = 3.33*(dolbyVolume-7)
        else: #dolbyVolume <=4
            db = 20*(dolbyVolume-4.5)
        #round to nearest tenth.
        db = round(db*10)/10
        return str(db)

    # Converts db to the ten point scale used by Dolby and JSD cinema processors
    def dbtodolby(self, dbVolume):
        try:
            dbVolume = float(dbVolume)
            if(dbVolume>10):
                dbVolume = 10
            elif(dbVolume<-90):
                dbVolume = -90

            if (dbVolume>-10):
                dolby = (dbVolume/3.33)+7
            else: #dbVolume <= -10
                dolby = (dbVolume/20)+4.5
            #round to nearest tenth.
            dolby = round(dolby*10)/10
            return str(dolby)
        except Exception as e:
            return False

    # Set Preset by number
    def setmacro(self, macro):
        macroID = int(macro)-1 #They index by zero internally, but index by one externally
        if macroID==-1:
            macroID = 9 #If someone presses the zero button, change it to select the 10th preset, id 9
        rawResponse = self.send(f'<?xml version="1.0"?><!--0000{109+len(str(macroID))}--><SET_S RT="C00" ID="0" L1PW="qsc"><ESS O="0x00290000" M="0" S="{str(macroID)}"/></SET_S>')
        if(not rawResponse or len(rawResponse) == 0):
            return False
        index0 = rawResponse.find(' S="')+4
        #print(f'i0: {index0}')
        indexF = rawResponse[index0:].find('"')+index0
        #print(f'iF: {indexF}')
        return macro

    def setmacrobyname (self, macro):
        self.setmacro(int(macro.split(" ")[1:]))

    def getmacro(self):
        attempts = 0
        index0 = -1
        while(index0 < 4 and attempts < 5): #Attempt to get the macro id 5 times,
            attempts += 1
            rawResponse = self.send('<?xml version="1.0"?><!--0000104--><GET_S RT="C00" ID="0" L1PW="qsc"><EGS O="0x00290000" M="0"/></GET_S>')
            if(not rawResponse or len(rawResponse) == 0):
                return False
            index0 = rawResponse.find(' S="')+4
        if(index0<4):
            return False

        #print(f'i0: {index0}')
        indexF = rawResponse[index0:].find('"')+index0
        #print(f'iF: {indexF}')
        #print("raw response: " +rawResponse)
        #print("response: " +rawResponse[index0:indexF])
        response = rawResponse[index0:indexF]
        if response.isdigit():
            return int(rawResponse[index0:indexF])+1
        else:
            return False

    def getmacroname(self):
        macroID = self.getmacro()
        if(not macroID):
            return False
        macroID = macroID-1
        hexMacro = (hex(macroID)[2:]).upper()
        if len(hexMacro)==1:
            hexMacro= "0"+hexMacro
        attempts = 0
        index0 = -1
        while(index0 < 5 and attempts < 5): #Attempt to get the macro id 5 times,
            attempts += 1
            rawResponse = self.send(f'<?xml version="1.0"?><!--0000104--><GET_S RT="C00" ID="0" L1PW="qsc"><EGS O="0x002A00{hexMacro}" M="0"/></GET_S>')
            if(not rawResponse or len(rawResponse) == 0):
                return False
            index0 = rawResponse.find(' ST="')+5
        if(index0 < 5): #" ST=" not found
            return ""
        #print(f'i0: {index0}')
        indexF = rawResponse[index0:].find('"')+index0
        #print(f'iF: {indexF}')
        macroName = rawResponse[index0:indexF]
        #print("Raw Response: " + rawResponse)
        #print("Macro name: " + macroName)
        if(len(macroName) == 0):
            return "Unnamed Preset " + str(macroID+1)
        return macroName

    def getmacrolist(self):
        macroList = (
            "Preset 1", "Preset 2", "Preset 3", "Preset 4", "Preset 5",
            "Preset 6", "Preset 7", "Preset 8", "Preset 9", "Preset 10",
            "Preset 11", "Preset 12", "Preset 13", "Preset 14", "Preset 15",
            "Preset 16", "Preset 17", "Preset 18", "Preset 19", "Preset 20",
            "Preset 21", "Preset 22", "Preset 23", "Preset 24", "Preset 25",
            "Preset 26",  "Preset 27", "Preset 28", "Preset 29", "Preset 30",
            "Preset 31", "Preset 32"
        )
        return macroList



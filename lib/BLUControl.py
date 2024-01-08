from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import CinemaProcessor
import binascii
import math

#ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

PORT = 1023
FADERID = "0060"
MUTEID = "0061"


def hexToDecimal(hexstr, bits):
    value = int("0x" + hexstr)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value

def decimalToHex(value, bits):
    hexval = hex((round(value) + (1 << bits)) % (1 << bits)).replace('0x','')
    hexval = "00000000" + hexval
    currentFader = -1
    return hexval[-8:]

class BLUControl(CinemaProcessor.CinemaProcessor):
    def __init__(self, host, newHiQnetAddress):
        super().__init__(host, PORT)
        self.HiQnetAddress = str(newHiQnetAddress).replace('0x', '')

    # Kind of cheating here
    def getState(self):
        if self.socket is not None:
            return "connected"
        else:
            return "disconnected"

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
            packet = str('02') + self.specialChar(command + self.checksum(command), 0) + str('03')

            #check_sum = self.checksum(command)
            # print("command:" + command + check_sum)
            # print("length: " + str(len(command + check_sum)))
            # print("sp char command: " + self.specialChar(command + check_sum, 0))
            # print("length: " + str(len(self.specialChar(command + check_sum, 0))))
            # print("packet: " + packet)
            # print("packet length: " + str(len(packet)))

            self.socket.send(binascii.unhexlify(packet))
            result = str(binascii.hexlify(self.socket.recv())).replace('b\'', '').replace('\'', '')
            result = self.specialChar(result, 1)
            return result
        except Exception as e:
            print("SEND Error: " + str(e))
            # print("command: " + command + self.checksum(command))
            # print("packet: " + packet)
            # print("packet length: " + str(len(packet)))
            return False

    def specialChar(self, subMsg, reverse):
        subs = {'02': '1b82', '03': '1b83', '06': '1b86', '15': '1b95', '1b': '1b9b'}
        subAry = [subMsg[i:i+2] for i in range(0, len(subMsg), 2)]  # Break data string into array of twos
        if reverse == 0:
            pos = 0
            for byte in subAry:
                for key, value in subs.items():
                    if key.lower() == byte.lower():
                        # print('found ' + byte + ' at position ' + str(pos))
                        # print('replacing with ' + value)
                        subAry[pos] = value
                pos += 1

            return "".join(subAry)

        elif reverse == 1:
            # print 'reverse equaled 1'
            pos = 0
            # print 'received byte array ' + str(subAry)

            for byte in subAry:
                # print 'checking byte ' + byte
                for key, value in subs.items():
                    if value[:2].lower() == byte.lower():  # if first two char of the value matches the current byte...
                        if value[2:].lower() == subAry[pos + 1]:
                            # print 'found byte ' + byte
                            subAry[pos] = key  # replace with key
                            # print str(subAry)
                            # print 'replaced byte with ' + key
                            # print 'removing ' + str(subAry[pos+1])
                            subAry.pop(pos + 1)  # remove byte in next position.
                        # print str(subAry)
                pos += 1

            # print 'returning byte string ' + "".join(subAry)
            return "".join(subAry)

    def checksum(self, packet):
        #print ('calculating checksum for: ' + packet)
        # print 'length: ' + str(len(packet))
        checksum = 0
        for byte in binascii.unhexlify(packet):
            #print(hex(byte))
            #checksum ^= ord(byte)
            checksum ^= byte
        #print("checksum calculated: " + str(hex(checksum)).replace('0x', ''))
        #print('Checksum: ' + str(hex(checksum)))

        ret_checksum = str(hex(checksum)).replace('0x', '')
        # add leading  zero, if needed.
        if len(ret_checksum) == 1:
            ret_checksum = '0'+ ret_checksum
        return ret_checksum

    # processing the response is sort of specific to the function in question, so I do not use this.
    # In retrospect, it seems unnecessary to have this as a shared function.
    def stripvalue(self, responseText):
        return responseText

    # Functional, but should make better use of subscribe rather than using it as a get command
    def getfader(self):
        messageType = '89'
        data = '00000000'
        #subscribe to master fader
        packet = messageType + self.HiQnetAddress + FADERID + data
        #print("get packet: " + packet)
        rawResponse = self.send(packet)
        if rawResponse:
            decValue = hexToDecimal(rawResponse[20:28], 32)
            if decValue >= -100000:
                dBVolume = decValue/10000
            elif decValue > -280617: #Calculated estimated logrithmic conversion. Needs improvement.
                dBVolume = 32.088*math.log(decValue+300000)-401.51
            else:
                dBVolume = -84
            #print("dB volume: " + str(dBVolume))
            fader = self.dbtodolby(dBVolume)
            #print("Dolby volume: " + str(fader))
            self.currentFader = fader
            #unsubscribe
            self.send(f'8A{self.HiQnetAddress}{FADERID}')
            return fader
        else:
            return False

    # TODO?
    def setfader(self, value):
        messageType = '88'
        # calculate data from value)
        # print("set Dolby volume: " + str(value))
        dBVolume = self.dolbytodb(value)
        # print("set dBVolume: " + str(dBVolume))
        if dBVolume <= -84:
            bluVolume = -280617
        elif dBVolume < -10:
            bluVolume = round(math.e**((dBVolume+401.51)/32.088)-300000)
        elif dBVolume >= 10:
            bluVolume = 100000
        else:
            bluVolume = dBVolume*10000
        # print("set BLU volume: " + str(bluVolume))
        data = decimalToHex(bluVolume, 32)
        # print("set BLU volume (hex): " + str(data))
        packet = messageType + self.HiQnetAddress + FADERID + data
        # print("get packet: " + packet)
        self.send(packet)


    def addfader(self, value=1):
        if (self.currentFader == -1):
            self.currentFader = self.getfader()
        if(value and self.currentFader):
            newFader = (self.currentFader * 10) + value
            if(newFader<5):
                self.currentFader = 0.5
                self.setfader(0.5)
            elif(newFader>100):
                self.currentFader = 10.0
                self.setfader(10.0)
            else:
                self.currentFader = newFader/10
                self.setfader(newFader/10)
            return True
        else:
            return False


    # TODO
    def setmute(self, mute=1):
        return 0

    # TODO
    def getmute(self):
        return 0

    # TODO
    def displayfader(self):
        fader = self.getfader()
        if(fader):
            return str(fader)
        else:
            return False

    # Converts the 0.0-10.0 scale used by the Dolby and JSD CPs to dB
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
        return db

    # Converts dB to the ten point scale used by Dolby and JSD cinema processors
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
            return dolby
        except Exception as e:
            return False
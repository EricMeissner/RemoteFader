import os
import displayio
import terminalio
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_st7735r import ST7735R
from adafruit_display_text import label
import digitalio
import rotaryio
import time
import math
import board
import busio
import keypad
import json

#from enum import Enum

# Network stuff
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

import CP650Control
import CP750Control
import CP850Control
import JSD60Control
import JSD100Control
import AP20Control
import DCPControl
import BLUControl

import Config

VERSION = "1.7.2"

#class ProgramState(Enum):
#    LOADING = 0
#    CONNECTING = 1
#    CONNECTED = 2
#    EDIT_CPTYPE = 3
#    EDIT_CPIP = 4
#    EDIT_OWNIP = 5
#    CONFIRM_CHANGE = 6
#    CHANGE_MACRO = 7
#    EDIT_KEYPAD_ENABLE = 8
#    TEST = 9
#    BROWSE_SAVED_PROFILES = 10
#    SELECT_EDIT_PROFILE = 11
#    EDIT_HIQNET = 12


# Types of Cinema Processors supported.
#class CPTypeCode(Enum):
#    CP650 = 0
#    CP750 = 1
#    CP850/950 = 2
#    JSD60 = 3
#    JSD100 = 4
#    AP20/24/25 = 5
#    DCP100-300 = 6
#    BLU = 7

CPCOUNT = 8

# Ethernet Stuff
SUBNET_MASK = Config.SUBNET_MASK
GATEWAY_ADDRESS = Config.GATEWAY_ADDRESS
DNS_SERVER = Config.DNS_SERVER

# Encoder Pins
DIR = Config.DIR
STEP = Config.STEP

ENCODER_BUTTON = Config.ENCODER_BUTTON

# Ethernet pins
SPI1_SCK = Config.SPI1_SCK
SPI1_TX = Config.SPI1_TX
SPI1_RX = Config.SPI1_RX
SPI1_CSn = Config.SPI1_CSn
W5500_RSTn = Config.W5500_RSTn

# Encoder Sensitivity
SENSITIVITY = Config.SENSITIVITY

# Cinema Processor
cp = None

new_cpType = None
new_cpIP = None
new_ownIP = None
new_formatEnable = None
new_HiQnetAddress = None
lastPosition = 0
fader = 0
mute = 0
macro = False

dropped_requests = 0
MAXDROPS = 15

if hasattr(Config, 'DISPLAY_TYPE'):
    DISPLAY_TYPE = Config.DISPLAY_TYPE
else:
    DISPLAY_TYPE = 1

# i2c stuff
if hasattr(Config, 'SDA'):
    SDA = Config.SDA
if hasattr(Config, 'SCL'):
    SCL = Config.SCL
if hasattr(Config, 'DEVICE_ADDRESS'):
    DEVICE_ADDRESS = Config.DEVICE_ADDRESS

# spi stuff
if hasattr(Config, 'SPI_CLOCK'):
    SPI_CLOCK = Config.SPI_CLOCK
if hasattr(Config, 'SPI_MOSI'):
    SPI_MOSI = Config.SPI_MOSI
if hasattr(Config, 'SPI_RESET'):
    SPI_RESET = Config.SPI_RESET
if hasattr(Config, 'SPI_CS'):
    SPI_CS = Config.SPI_CS
if hasattr(Config, 'SPI_DC'):
    SPI_DC = Config.SPI_DC

if hasattr(Config, 'DISPLAY2_WIDTH'):
    DISPLAY2_WIDTH = Config.DISPLAY2_WIDTH
else:
    DISPLAY2_WIDTH = 128
if hasattr(Config, 'DISPLAY2_HEIGHT'):
    DISPLAY2_HEIGHT = Config.DISPLAY2_HEIGHT
else:
    DISPLAY2_HEIGHT = 160

if hasattr(Config, 'TEXT_COLOR') and DISPLAY_TYPE == 2: #Display type 1 is monochrome
    TEXT_COLOR = Config.TEXT_COLOR
else:

    TEXT_COLOR = 0xFFFFFF
if hasattr(Config, 'DISPLAY_COLOR') and DISPLAY_TYPE == 2:
    DISPLAY_COLOR = Config.DISPLAY_COLOR
else:
    DISPLAY_COLOR = TEXT_COLOR
if hasattr(Config, 'HEADER_COLOR') and DISPLAY_TYPE == 2:
    HEADER_COLOR = Config.HEADER_COLOR
else:
    HEADER_COLOR = TEXT_COLOR


# Keypad stuff
if hasattr(Config, 'KEYPAD_EXISTS'):
    KEYPAD_EXISTS = Config.KEYPAD_EXISTS
else:
    KEYPAD_EXISTS = False
if hasattr(Config, 'FORMAT_KEY'):
    FORMAT_KEY = Config.FORMAT_KEY
else:
    FORMAT_KEY = "A"
if hasattr(Config, 'MUTE_KEY'):
    MUTE_KEY = Config.MUTE_KEY
else:
    MUTE_KEY = False
if hasattr(Config, 'UNMUTE_KEY'):
    UNMUTE_KEY = Config.UNMUTE_KEY
else:
    UNMUTE_KEY = False
if hasattr(Config, 'KEYPAD_EXISTS'):
    KEYPAD_EXISTS = Config.KEYPAD_EXISTS
else:
    KEYPAD_EXISTS = False

large_font = True

# Extract saved data from data.txt
# Obsolete
def getData():
    global ownIP, cpIP, cpType, formatEnable
    #Setting arbitrary defaults, in case the data file is bad
    cpType = 0
    cpIP =  "192.168.1.128"
    ownIP = "192.168.1.149"
    #keypadEnable = KEYPAD_EXISTS
    formatEnable = KEYPAD_EXISTS
    try:
        with open('data.txt', 'r') as file:
            data = file.readlines()

        # Scan data file line by line
        for x in data:
            #determine if the line is defining a variable and what variable it is.
            #Split the line by whitespace, take the second text string (the value)
            #TODO: Basic validation
            if x.startswith('cpType:'):
                cpType = int(x.split()[1])
                if (cpType >= CPCOUNT):
                    cpType = 0
            elif x.startswith('cpIP:'):
                cpIP = x.split()[1]
            elif x.startswith('ownIP:'):
                # after extracting ownIP, split it into a tuple of ints
                ownIP = x.split()[1]
            elif x.startswith('keypadEnable:') or x.startswith('formatEnable'):
                formatEnable = bool(int(x.split()[1]))
    except Exception as ex:
        pass

# Extract saved data from data.json
def getJSONData():
    global profiles, current_profile
    try:
        with open('data.json', 'r') as file:
            jsondata = json.load(file)
            current_profile = jsondata["current_profile"]
            profiles = jsondata["profiles"]
    except Exception as ex:
        #TODO: Make default blank values'
        pass

# Save settings data to data.txt
# Obsolete
def saveData():
    #global ownIP,cpIP,cpType,keypadEnable
    try:
        with open('data.txt', 'w') as file:
            file.write(f'cpType: {str(cpType)}\n')
            file.write(f'cpIP: {cpIP}\n')
            file.write(f'ownIP: {ownIP}\n')
            file.write(f'formatEnable: {str(int(formatEnable))}\n')
    except Exception as ex:
        pass

# Save settings data to data.json
def saveJSONData():
    #global ownIP,cpIP,cpType,keypadEnable
    try:
        with open('data.json', 'w') as file:
            data = {
                "current_profile": current_profile,
                "profiles": profiles
            }
            json.dump(data, file)
    except Exception as ex:
        pass

def setupEthernet():
    global eth

    ownIP = profiles[current_profile]["ownIP"]

    ethernetRst = digitalio.DigitalInOut(W5500_RSTn)
    ethernetRst.direction = digitalio.Direction.OUTPUT

    cs = digitalio.DigitalInOut(SPI1_CSn)

    spi_bus = busio.SPI(SPI1_SCK, MOSI=SPI1_TX, MISO=SPI1_RX)

    # Reset W5500 first
    ethernetRst.value = False
    time.sleep(1)
    ethernetRst.value = True

    eth = WIZNET5K(spi_bus, cs, is_dhcp=False)

    # Set network configuration
    IP = tuple(map(int, ownIP.split('.')))
    eth.ifconfig = ([IP, SUBNET_MASK, GATEWAY_ADDRESS, DNS_SERVER])
    socket.set_interface(eth)

def manageProfiles():
    global pState, current_profile, enc
    pState = 10
    enc.position = int(current_profile / SENSITIVITY)
    refreshDisplay()
    while (not encbtn.value):
        pass
    while encbtn.value:
        current_profile = math.floor(enc.position*SENSITIVITY) % len(profiles)
        refreshDisplay()
    pState = 11
    enc.position = 0
    refreshDisplay()
    while (not encbtn.value):
        pass
    while (encbtn.value or enc.position == 0):
        refreshDisplay()
    if (enc.position < 0):
        editIP()
    elif (enc.position > 0):
        saveJSONData()
        pState = 0
        refreshDisplay()


# Edit settings
def editIP():
    global pState, new_cpIP, new_ownIP, new_cpType, new_formatEnable, currentOctet, enc, encbtn, profiles, displayHiQ, new_HiQnetAddress, HiQindex
    pState = 3  #Edit cpType
    if (new_cpType is None):
        new_cpType = profiles[current_profile]["cpType"]
    if (new_cpIP is None):
        new_cpIP = list(map(int, profiles[current_profile]["cpIP"].split('.')))
    if (new_ownIP is None):
        new_ownIP = list(map(int, profiles[current_profile]["ownIP"].split('.')))
    if (new_formatEnable is None):
        new_formatEnable = int(profiles[current_profile]["formatEnable"])
    if (new_HiQnetAddress is None):
        try:
            new_HiQnetAddress = profiles[current_profile]["HiQnetAddress"]
        except Exception as e:
            new_HiQnetAddress = "000000000000"
    enc.position = int(new_cpType/SENSITIVITY)
    refreshDisplay()
    while(not encbtn.value):
        pass
    while(encbtn.value):
        if KEYPAD_EXISTS:   #Include test mode option
            new_cpType = math.floor(enc.position*SENSITIVITY) % (CPCOUNT+1)
        else:
            new_cpType = math.floor(enc.position * SENSITIVITY) % CPCOUNT
        #if not macroChangeImplemented(new_cpType):
        #    new_formatEnable = 0
        refreshDisplay()
    if new_cpType == CPCOUNT:
        pState = 9
        testKeypad()
    elif new_cpType == 7:   # BLU
        pState = 12         # Edit HiQNet Address
        HiQindex = 0
        displayHiQ = '>' + new_HiQnetAddress
        #HiQchar = int(new_HiQnetAddress[0]/SENSITIVITY)
        refreshDisplay()
        while (not encbtn.value):
            pass
        while (HiQindex < 12):
            enc.position = int(int("0x" + new_HiQnetAddress[HiQindex]) / SENSITIVITY)
            while (not encbtn.value):
                pass
            while (encbtn.value):
                HiQchar = hex(math.floor(enc.position * SENSITIVITY) % 16).replace('0x', '')
                if HiQindex == 0:
                    displayHiQ = '>' + str(HiQchar) + new_HiQnetAddress[1:]
                elif HiQindex == 11:
                    displayHiQ = new_HiQnetAddress[:11] + '>' + str(HiQchar)
                else:
                    displayHiQ = new_HiQnetAddress[:HiQindex] + '>' + str(HiQchar) + new_HiQnetAddress[HiQindex+1:]
                refreshDisplay()
            if HiQindex == 0:
                new_HiQnetAddress = HiQchar + new_HiQnetAddress[1:]
            elif HiQindex == 11:
                new_HiQnetAddress = new_HiQnetAddress[:11] + HiQchar
            else:
                new_HiQnetAddress = new_HiQnetAddress[:HiQindex] + HiQchar + new_HiQnetAddress[HiQindex+1:]
            HiQindex += 1
            refreshDisplay()

    pState = 4
    currentOctet = 0
    refreshDisplay()
    # first octet (octet[0]) should only be 10 or 192 for private networks
    firstOctetChoices = 3
    oldFirstOctet = new_cpIP[0]
    if(new_cpIP[0] == 10):
        enc.position = 0
    elif(new_cpIP[0] == 192):
        enc.position = int(1/SENSITIVITY)
    elif(new_cpIP[0] in range(256)):
        enc.position = int(3/SENSITIVITY)
        firstOctetChoices = 4
    else:
        print("Invalid IP: Defaulting to 10")
        enc.position = 0
    refreshDisplay()
    while(not encbtn.value):
        pass
    while(encbtn.value):
        p = math.floor(enc.position*SENSITIVITY) % firstOctetChoices
        if(p==0):
            new_cpIP[0] = 10
        elif(p==1):
            new_cpIP[0] = 192
        elif (p == 2):
            new_cpIP[0] = "???"
        elif (p == 3):
            new_cpIP[0] = oldFirstOctet
        refreshDisplay()
    if(new_cpIP[0] == 192):
        new_cpIP[1] = 168
        currentOctet = 2
    elif(new_cpIP[0] == "???"): #Custom 1st octet
        new_cpIP[0] = 0
        currentOctet = 0
    else:
        currentOctet = 1
    refreshDisplay()
    while(currentOctet<4):
        enc.position = int(new_cpIP[currentOctet]/SENSITIVITY)
        while(not encbtn.value):
            pass
        while(encbtn.value):
            new_cpIP[currentOctet] = math.floor(enc.position*SENSITIVITY) % 255
            refreshDisplay()
        currentOctet += 1
        refreshDisplay()
    pState = 5
    currentOctet = 3
    refreshDisplay()
    enc.position = int(new_ownIP[currentOctet]/SENSITIVITY)
    for i in range(3):
        new_ownIP[i] = new_cpIP[i]
    while(not encbtn.value):
        pass
    while(encbtn.value):
        new_ownIP[currentOctet] = math.floor(enc.position*SENSITIVITY) % 255
        refreshDisplay()
    currentOctet += 1

    pState = 8
    enc.position = int(new_formatEnable/SENSITIVITY)
    refreshDisplay()
    while(not encbtn.value):
        pass
    while(encbtn.value):
        new_formatEnable = math.floor(enc.position*SENSITIVITY) % 2
        refreshDisplay()
    pState = 6
    enc.position = 0
    refreshDisplay()
    while(not encbtn.value):
        pass
    while(encbtn.value or enc.position == 0):
        refreshDisplay()
    if(enc.position<0):
        editIP()
    elif(enc.position>0):
        profiles[current_profile]["cpType"] = new_cpType
        profiles[current_profile]["cpIP"] = '.'.join(map(str, new_cpIP))
        profiles[current_profile]["ownIP"] = '.'.join(map(str, new_ownIP))
        profiles[current_profile]["formatEnable"] = bool(new_formatEnable)
        profiles[current_profile]["HiQnetAddress"] = new_HiQnetAddress
        saveJSONData()
        pState = 0
        refreshDisplay()
    else:
        print("This should not be able to happen.")

##########################################################################

# Sets up the OLED display.
def setUpDisplay():
    global header, label_1, label_2, label_3, label_4, faderDisplay, big_label_1, big_label_2

    displayio.release_displays()
    if DISPLAY_TYPE == 1:
        i2c = busio.I2C(SCL, SDA)
        display_bus = displayio.I2CDisplay(i2c, device_address=DEVICE_ADDRESS)
        display = SSD1306(display_bus, width=128, height=64)

    elif DISPLAY_TYPE == 2:
        spi = busio.SPI(clock=SPI_CLOCK, MOSI=SPI_MOSI)
        display_bus = displayio.FourWire(spi, command=SPI_DC, chip_select=SPI_CS, reset=SPI_RESET)
        display = ST7735R(display_bus, width=DISPLAY2_WIDTH, height=DISPLAY2_HEIGHT, bgr = True)
        display.rotation=90
    else:
        print("Invalid DISPLAY_TYPE. This shouldn't happen, see Config.py.")


    # Make the display context
    group = displayio.Group()
    display.show(group)
    header = label.Label(
        terminalio.FONT, text="", color=HEADER_COLOR, x=2, y=8
    )
    label_1 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=20
    )
    label_2 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=32
    )
    label_3 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=44
    )
    label_4 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=56
    )
    label_4 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=56
    )
    faderDisplay = label.Label(
        terminalio.FONT, text="", color=DISPLAY_COLOR, x=5, y=36
    )
    big_label_1 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=22, scale=2
    )
    big_label_2 = label.Label(
        terminalio.FONT, text="", color=TEXT_COLOR, x=2, y=46, scale=2
    )
    if(DISPLAY_TYPE==1):            #SSD1306
        faderDisplay.scale=5
    else:   #DISPLAY_TYPE == 2      #ST7735R
        faderDisplay.scale=6
    #if(KEYPAD_EXISTS):
    #    faderDisplay.scale = 4
    #    faderDisplay.y = 28
    group.append(header)
    group.append(label_1)
    group.append(label_2)
    group.append(label_3)
    group.append(label_4)
    group.append(faderDisplay)
    group.append(big_label_1)
    group.append(big_label_2)

    refreshDisplay()


# Update the OLED display with what the current state of the program is.
# After you change the program state or any of the displayed variables on the OLEd
# you'll need to call this to update the OLED to show the changes.
def refreshDisplay():
    global header, label_1, label_2, label_3, label_4, faderDisplay, big_label_1, big_label_2

    header_text = ""
    label_1_text = ""
    label_2_text = ""
    label_3_text = ""
    label_4_text = ""
    faderDisplay_text = ""
    big_label_1_text = ""
    big_label_2_text = ""

    if(pState == 0): #Loading
        header_text = "Loading..."
    elif(pState in (1,10,11)): #Connecting, Profile browse, select/edit profile
        label_1_text = f'CP Type: {getCPTypeFromCode(profiles[current_profile]["cpType"])}'
        label_2_text = f'CPIP:{profiles[current_profile]["cpIP"]}'
        label_3_text = f'FIP: {profiles[current_profile]["ownIP"]}'
        label_4_text = f'Enable Format: {str(profiles[current_profile]["formatEnable"])}'
        if pState == 1:
            header_text = "Connecting..."
        elif pState in (10, 11):
            header_text = f'Profile '
            if (pState == 10):
                header_text += f'>{current_profile} v{VERSION}'
            elif (pState == 11):
                header_text += f'{current_profile}'
                if (enc.position < 0):
                    header_text += ' EDIT'
                elif (enc.position > 0):
                    header_text += ' LOAD'
                else:
                    header_text += ' EDIT/LOAD'
    elif(pState in (2,7)): #2: Connected state; 7: Change format
        header_text = f'Connected-{getCPTypeFromCode(profiles[current_profile]["cpType"])}'
        if(MUTE_KEY):
            if(getMute()):
                faderDisplay_text += "M "
        faderDisplay_text += getDisplayFader()
        if(profiles[current_profile]["formatEnable"]):
            macroname = macro #getmacroname returns False for CPs where this functionality is not yet supported
            if(macroname != False):
                if(DISPLAY_TYPE==1):        #SSD1306
                    faderDisplay.scale = 4
                    faderDisplay.y = 28
                else:   #DISPLAY_TYPE == 2  #ST7735R
                    faderDisplay.scale = 6
                    faderDisplay.y = 38
                    label_4.y = 80
                if(pState == 2):
                    if macroname == "":
                        label_4_text = label_4.text
                    else:
                        label_4_text = macroname
                elif(pState == 7):
                    label_4_text = f'F> {macrolist[newMacroIndex]}'
            else:
                if(DISPLAY_TYPE==1):        #SSD1306
                    faderDisplay.scale = 5
                    faderDisplay.y = 36
                else:   #DISPLAY_TYPE == 2  #ST7735R
                    faderDisplay.scale = 6
                    faderDisplay.y = 38
    elif(pState in (3,4,5,6,8,12)):
        if (large_font and pState != 6) or pState == 12:
            header_text = "Edit: "
            if(pState == 3):
                header_text += "CP Type"
                big_label_1_text = getCPTypeFromCode(new_cpType)
                label_4_text = f'Version: {VERSION}'
            elif pState == 4:
                header_text += "CP IP"
                if currentOctet == 0:
                    big_label_1_text = f'>{new_cpIP[0]}.{new_cpIP[1]}.'
                    big_label_2_text = f'{new_cpIP[2]}.{new_cpIP[3]}'
                elif currentOctet == 1:
                    big_label_1_text = f'{new_cpIP[0]}.>{new_cpIP[1]}.'
                    big_label_2_text = f'{new_cpIP[2]}.{new_cpIP[3]}'
                elif currentOctet == 2:
                    big_label_1_text = f'{new_cpIP[0]}.{new_cpIP[1]}.'
                    big_label_2_text = f'>{new_cpIP[2]}.{new_cpIP[3]}'
                elif currentOctet == 3:
                    big_label_1_text = f'{new_cpIP[0]}.{new_cpIP[1]}.'
                    big_label_2_text = f'{new_cpIP[2]}.>{new_cpIP[3]}'
            elif pState == 5:
                header_text += "Fader IP"
                if currentOctet == 0:
                    big_label_1_text = f'>{new_ownIP[0]}.{new_ownIP[1]}.'
                    big_label_2_text = f'{new_ownIP[2]}.{new_ownIP[3]}'
                elif currentOctet == 1:
                    big_label_1_text = f'{new_ownIP[0]}.>{new_ownIP[1]}.'
                    big_label_2_text = f'{new_ownIP[2]}.{new_ownIP[3]}'
                elif currentOctet == 2:
                    big_label_1_text = f'{new_ownIP[0]}.{new_ownIP[1]}.'
                    big_label_2_text = f'>{new_ownIP[2]}.{new_ownIP[3]}'
                elif currentOctet == 3:
                    big_label_1_text = f'{new_ownIP[0]}.{new_ownIP[1]}.'
                    big_label_2_text = f'{new_ownIP[2]}.>{new_ownIP[3]}'
            elif pState == 8:
                header_text = "Enable Format Change?"
                big_label_1_text = str(bool(new_formatEnable))
                if not macroChangeImplemented(new_cpType):
                    label_4_text = 'Function unavailable'
            elif pState == 12:
                header_text = "HiQNet Address"
                if HiQindex < 6:
                    big_label_1_text = displayHiQ[:7].upper()
                    big_label_2_text = displayHiQ[7:].upper()
                else:
                    big_label_1_text = displayHiQ[:6].upper()
                    big_label_2_text = displayHiQ[6:].upper()

        else:
            header_text = f'Edit Setup v{VERSION}'
            if(pState == 3):
                label_1_text = f'CP Type: >{getCPTypeFromCode(new_cpType)}'
            else:
                label_1_text = f'CP Type: {getCPTypeFromCode(new_cpType)}'
            label_2_text = 'CPIP:'
            for i in range(4):
                if(pState==4 and currentOctet == i):
                    label_2_text += '>'
                label_2_text += str(new_cpIP[i])
                if(i!=3):
                    label_2_text += '.'
            label_3_text = 'FIP: '
            for i in range(4):
                if(pState==5 and currentOctet == i):
                    label_3_text += '>'
                label_3_text += str(new_ownIP[i])
                if(i!=3):
                    label_3_text += '.'
            if(pState == 8):
                label_4_text = f'Enable Format: >{str(bool(new_formatEnable))}'
            else:
                label_4_text = f'Enable Format: {str(bool(new_formatEnable))}'
            if(pState == 6):
                header_text = 'Confirm? '
                if(enc.position<0):
                    header_text += 'NO'
                elif(enc.position>0):
                    header_text += 'YES'
                else:
                    header_text += 'NO/YES'

    elif pState == 9:
        header_text = "TEST KEYPAD"
        big_label_1_text = testString[:8]
        big_label_2_text = testString[8:]
    else:
        header_text = "Program State hasn't been defined yet"
        label_1_text = f'pState = {pState}'

    header.text = header_text
    label_1.text = label_1_text
    label_2.text = label_2_text
    label_3.text = label_3_text
    label_4.text = label_4_text
    faderDisplay.text = faderDisplay_text
    big_label_1.text = big_label_1_text
    big_label_2.text = big_label_2_text

def constructCinemaProcessorObject():
    global cp, delay
    if(cp is not None):
        if(cp.getState() == "connected"):
            cp.disconnect()
        cp = None
    # Polling rate
    delay=Config.POLLING_DELAY
    cpType = profiles[current_profile]["cpType"]
    cpIP = profiles[current_profile]["cpIP"]
    if(cpType==0):
        cp = CP650Control.CP650Control(cpIP)
    elif(cpType==1):
        cp = CP750Control.CP750Control(cpIP)
    elif(cpType==2):
        cp = CP850Control.CP850Control(cpIP)
    elif(cpType==3):
        cp = JSD60Control.JSD60Control(cpIP)
    elif(cpType==4):
        cp = JSD100Control.JSD100Control(cpIP)
    elif(cpType==5):
        cp = AP20Control.AP20Control(cpIP)
    elif(cpType==6):
        cp = DCPControl.DCPControl(cpIP)
    elif (cpType == 7):
        cp = BLUControl.BLUControl(cpIP, profiles[current_profile]["HiQnetAddress"])
    else:
        print("Error: invalid CP type")

def setUpCinemaProcessor():
    global cp, pState, macrolist
    constructCinemaProcessorObject()
    macrolist = cp.getmacrolist()
    pState = 1
    refreshDisplay()
    cp.connect()
    #Check to see if the Cinema Processor is connected and if it isn't, keep trying each 1 second
    while cp.getState() != 'connected':
        time.sleep(1) #Consider making this configurable?
        cp.connect()
    pState = 2
    refreshDisplay()

def getCPTypeFromCode(code):
    if(code==0):
        return 'CP650'
    elif(code==1):
        return  'CP750'
    elif(code==2):
        return  'CP850/950'
    elif(code==3):
        return  'JSD60'
    elif(code==4):
        return  'JSD100'
    elif(code==5):
        return  'AP20/24/25'
    elif(code==6):
        return  'DCP100-300'
    elif (code == 7):
        return 'BLU'
    else:
        return 'TEST KEYS'

def changeMacro():
    global newMacroIndex, pState, enc, encbtn, km, KEYS
    pState = 7
    cpType = profiles[current_profile]["cpType"]
    newMacroIndex = getMacroIndex()
    refreshDisplay()
    enc.position = int(newMacroIndex/SENSITIVITY)
    while(encbtn.value):
        newMacroIndex = math.floor(enc.position*SENSITIVITY) % len(macrolist)
        refreshDisplay()
    #cp.setmacrobyname(macrolist[newMacroIndex])
    if cpType in (1,2):
        cp.setmacrobyname(macrolist[newMacroIndex])
    elif cpType in (0,6):
        cp.setmacro(newMacroIndex+1)
    else:
        print("Macro/preset/input change not supported/implemented. Eric, change the changeMacro() function!")

    #Reset encoder position
    enc.position = 0
    #Clear out the button presses in case someone pressed A a few times
    if(KEYPAD_EXISTS):
        event = km.events.get()
        while event:
            event = km.events.get()

    pState = 2
    refreshDisplay()

def macroChangeImplemented(typecp):
    return typecp in (0,1,2,6)

#
def getMacroIndex():
    macroIndex = 0
    cpType = profiles[current_profile]["cpType"]
    if cpType in (1,2):
        macroIndex = macrolist.index(cp.getmacroname())
    elif cpType == 6:
        macroIndex = cp.getmacro()-1
    return macroIndex

def testKeypad():
    global testString, km
    testString = ''
    refreshDisplay()
    while True:
        if KEYPAD_EXISTS:
            event = km.events.get()
            while event:
                keyPressed = KEYS[event.key_number]
                if event.pressed:
                    testString += keyPressed
                event = km.events.get()
            if not encbtn.value:
                testString = ''
        else:
            testString = "Keypad disabled in CONFIG"
        refreshDisplay()

def getDisplayFader():
    global lastPosition
    if pState == 7:
        lastPosition = 0
        return fader
    else:
        currentPosition = enc.position
        positionChanges = currentPosition - lastPosition
        volumeChange = math.floor(positionChanges * SENSITIVITY)
        displayfader = round(float(fader)*10 + volumeChange)/10
        if displayfader > 10:
            return "10.0"
        elif displayfader < 0:
            return "0.5"
        else:
            return str(displayfader)

def getMute():
    return mute

def main():
    global cp, pState, enc, encbtn, km, KEYS, lastPosition, fader, mute, macro
    pState = 0

    setUpDisplay()
    # Load settings from data.txt
    getJSONData()
    if (KEYPAD_EXISTS):
        km = keypad.KeyMatrix(row_pins=Config.ROW_PINS, column_pins=Config.COLUMN_PINS)
        KEYS = Config.KEYS
    encbtn = digitalio.DigitalInOut(ENCODER_BUTTON)
    encbtn.direction = digitalio.Direction.INPUT
    encbtn.pull = digitalio.Pull.UP
    enc = rotaryio.IncrementalEncoder(STEP, DIR)

    # Enter editIP by holding button on startup
    if(not encbtn.value):
        manageProfiles()
        #editIP()
    formatEnable = profiles[current_profile]["formatEnable"]
    cpType = profiles[current_profile]["cpType"]
    setupEthernet()
    setUpCinemaProcessor()
    enc.position = 0
    lastPosition = 0
    lastUpdate = 0
    dropped_requests = 0
    fader = cp.displayfader()
    while 1==1:
        if dropped_requests > MAXDROPS:
            enc.position = 0
            lastPosition = 0
            setUpCinemaProcessor()

        if KEYPAD_EXISTS:
            event = km.events.get()
            while event:
                keyPressed = KEYS[event.key_number]
                if event.pressed:
                    print(keyPressed)
                    if formatEnable:
                        if keyPressed.isdigit():
                            cp.setmacro(keyPressed)
                        elif (keyPressed == FORMAT_KEY and len(macrolist) and macroChangeImplemented(cpType)):
                            changeMacro()
                    if MUTE_KEY:
                        if keyPressed == MUTE_KEY:
                            mute = 1
                            cp.setmute(1)
                        elif keyPressed == UNMUTE_KEY:
                            mute = 0
                            cp.setmute(0)
                event = km.events.get()
        elif (not encbtn.value and len(macrolist) and macroChangeImplemented(cpType) and formatEnable):
            while(not encbtn.value): #Wait until the button is released to prevent multiple input
                pass
            changeMacro()
        currentPosition = enc.position
        positionChanges = currentPosition - lastPosition
        volumeChange = math.floor(positionChanges * SENSITIVITY)
        if (time.monotonic() - lastUpdate) > delay:
            # If the position of the encoder changed, add/subtract it from the fader (modified by sensitivity)
            # Then adjust the position tracking value accordingly (used to be set back to zero, but
            # the sensitivity value would risk dropping half-ticks and the like.
            lastPosition = currentPosition
            mute = cp.getmute()
            if (volumeChange != 0):
                #time.sleep(0.1)
                cp.addfader(volumeChange)
                #time.sleep(0.1)
            lastPosition = currentPosition
            newFader = cp.displayfader()
            if (newFader):
                dropped_requests = 0
                lastUpdate = time.monotonic()
                fader = newFader
            else:
                # If there is a bad response, keep the old fader text and increment the drops
                # Don't reset last update to ensure you check again.
                dropped_requests += 1
                fader = round(float(fader)*10 + volumeChange)/10
            if (profiles[current_profile]["formatEnable"]):
                macro = cp.getmacroname()
            lastUpdate = time.monotonic()
        #Update the display with the current value
        refreshDisplay()
    # When the program is terminated, disconnect from the Cinema Processor and clear the displays.
    #cp.disconnect()

if __name__ == '__main__':
    main()

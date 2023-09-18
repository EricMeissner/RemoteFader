import os
import displayio
import terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import digitalio
import rotaryio
import time
import math
import board
import busio
import keypad

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

import Config

VERSION = "1.3.4"

#class ProgramState(Enum):
#    LOADING = 0
#    CONNECTING = 1
#    CONNECTED = 2
#    EDIT_CPTYPE = 3
#    EDIT_CPIP = 4
#    EDIT_OWNIP = 5
#    CONFIRM_CHANGE = 6


# Types of Cinema Processors supported.
#class CPTypeCode(Enum):
#    CP650 = 0
#    CP750 = 1
#    CP850/950 = 2
#    JSD60 = 3
#    JSD100 = 4
#    AP20/24/25 = 5
#    DCP100 = 6
#    DCP200 = 7
#    DCP300 = 8
#    DPM100 = 9
CPCOUNT = 10

# I2C pins
SDA = Config.SDA
SCL = Config.SCL

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



DEVICE_ADDRESS = Config.DEVICE_ADDRESS

DISPLAYWIDTH = Config.DISPLAYWIDTH
DISPLAYHEIGHT = Config.DISPLAYHEIGHT

# Cinema Processor
cp = None

new_cpType = None
new_cpIP = None
new_ownIP = None

dropped_requests = 0
MAXDROPS = 10
if hasattr(Config, 'KEYPAD_EXISTS'):
    KEYPAD_EXISTS = Config.KEYPAD_EXISTS
else:
    KEYPAD_EXISTS = False
# Extract saved data from data.txt
def getData():
    global ownIP, cpIP, cpType
    try:
        with open('data.txt', 'r') as file:
            data = file.readlines()

        # Scan data file line by line
        for x in data:
            #determine if the line is defining a variable and what variable it is.
            #Split the line by whitespace, take the second text string (the value), and remove any quotes
            #TODO: Basic validation
            if x.startswith('cpType:'):
                cpType = int(x.split()[1])
            elif x.startswith('cpIP:'):
                cpIP = x.split()[1]
            elif x.startswith('ownIP:'):
                # after extracting ownIP, split it into a tuple of ints
                ownIP = x.split()[1]

    except Exception as ex:
        pass

# Save settings data to data.txt
def saveData():
    global ownIP,cpIP,cpType
    try:

        with open('data.txt', 'w') as file:
            file.write(f'cpType: {str(cpType)}\n')
            file.write(f'cpIP: {cpIP}\n')
            file.write(f'ownIP: {ownIP}\n')

    except Exception as ex:
        pass

def setupEthernet():
    global eth

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

def editIP():
    global pState, new_cpIP, new_ownIP, cpIP, ownIP, cpType, new_cpType, currentOctet, enc, encbtn
    pState = 3
    if (new_cpType is None):
        new_cpType = cpType
    if (new_cpIP is None):
        new_cpIP = list(map(int, cpIP.split('.')))
    if (new_ownIP is None):
        new_ownIP = list(map(int, ownIP.split('.')))
    enc.position = int(new_cpType/SENSITIVITY)
    refreshDisplay()
    while(not encbtn.value):
        pass
    while(encbtn.value):
            new_cpType = math.floor(enc.position*SENSITIVITY) % CPCOUNT
            refreshDisplay()

    pState = 4
    currentOctet = 0
    refreshDisplay()
    # first octet (octet[0]) should only be 10 or 192 for private networks
    if(new_cpIP[0] == 10):
        enc.position = 0
    elif(new_cpIP[0] == 192):
        enc.position = int(1/SENSITIVITY)
    else:
        print("Invalid IP: Defaulting to 10")
        enc.position = 0
    while(not encbtn.value):
        pass
    while(encbtn.value):
        p = math.floor(enc.position*SENSITIVITY) % 2
        if(p==0):
            new_cpIP[0] = 10
        else:
            new_cpIP[0] = 192
        refreshDisplay()
    if(new_cpIP[0] == 192):
        new_cpIP[1] = 168
        currentOctet = 2
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
        cpType = new_cpType
        cpIP = '.'.join(map(str, new_cpIP))
        ownIP = '.'.join(map(str, new_ownIP))
        saveData()
        pState = 0
        refreshDisplay()
    else:
        print("This should not be able to happen.")

##########################################################################

# Sets up the OLED display.
def setUpDisplay():
    global header, label_1, label_2, label_3, label_4, faderDisplay

    displayio.release_displays()
    i2c = busio.I2C(SCL, SDA)
    display_bus = displayio.I2CDisplay(i2c, device_address=DEVICE_ADDRESS)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=DISPLAYWIDTH, height=DISPLAYHEIGHT)

    # Make the display context
    group = displayio.Group()
    display.show(group)
    header = label.Label(
        terminalio.FONT, text="", color=0xFFFFFF, x=2, y=8
    )
    label_1 = label.Label(
        terminalio.FONT, text="", color=0xFFFFFF, x=2, y=20
    )
    label_2 = label.Label(
        terminalio.FONT, text="", color=0xFFFFFF, x=2, y=32
    )
    label_3 = label.Label(
        terminalio.FONT, text="", color=0xFFFFFF, x=2, y=44
    )
    label_4 = label.Label(
        terminalio.FONT, text="", color=0xFFFFFF, x=2, y=56
    )
    faderDisplay = label.Label(
        terminalio.FONT, text="", color=0xFFFFFF, x=5, y=36, scale=5
    )
    if(KEYPAD_EXISTS):
        faderDisplay.scale = 4
        faderDisplay.y = 28
    group.append(header)
    group.append(label_1)
    group.append(label_2)
    group.append(label_3)
    group.append(label_4)
    group.append(faderDisplay)

    refreshDisplay()


# Update the OLED display with what the current state of the program is.
# After you change the program state or any of the displayed variables on the OLEd
# you'll need to call this to update the OLED to show the changes.
def refreshDisplay():

    #color_bitmap = displayio.Bitmap(DISPLAYWIDTH, DISPLAYHEIGHT, 1)
    #color_palette = displayio.Palette(1)
    #color_palette[0] =  0x000000  # Black

    #bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    #splash.append(bg_sprite)
    global header, label_1, label_2, label_3, label_4, faderDisplay, dropped_requests

    header_text = ""
    label_1_text = ""
    label_2_text = ""
    label_3_text = ""
    label_4_text = ""
    faderDisplay_text = ""

    if(pState == 0):
        header_text = "Loading..."
    elif(pState == 1):
        header_text = "Connecting..."
        label_1_text = f'CP Type: {getCPTypeFromCode(cpType)}'
        label_2_text = f'CPIP:{cpIP}'
        label_3_text = f'FIP: {eth.pretty_ip(eth.ip_address)}'
    elif(pState == 2):
        header_text = f'Connected-{getCPTypeFromCode(cpType)}'
        fader = cp.displayfader()
        if(fader):
            dropped_requests = 0
            faderDisplay_text = f'{fader}'
        else:
            # If there is a bad response, keep the old fader text.
            dropped_requests += 1
            faderDisplay_text = faderDisplay.text
        if(KEYPAD_EXISTS):
            label_4_text = cp.getmacroname()
    elif(pState in (3,4,5,6)):
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

        if(pState == 6):
            header_text = 'Confirm? '
            if(enc.position<0):
                header_text += 'NO'
            elif(enc.position>0):
                header_text += 'YES'
            else:
                header_text += 'NO/YES'
    else:
        header_text = "Program State hasn't been defined yet"
        label_1_text = f'pState = {pState.name}'

    header.text = header_text
    label_1.text = label_1_text
    label_2.text = label_2_text
    label_3.text = label_3_text
    label_4.text = label_4_text
    faderDisplay.text = faderDisplay_text

def constructCinemaProcessorObject():
    global cp, delay
    if(cp is not None):
        if(cp.getState() == "connected"):
            cp.disconnect()
        cp = None
    # Polling rate
    delay=Config.POLLING_DELAY
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
        #delay = 1
        cp = DCPControl.DCPControl(cpIP, "dcp100")
    elif(cpType==7):
        cp = DCPControl.DCPControl(cpIP, "dcp200")
    elif(cpType==8):
        cp = DCPControl.DCPControl(cpIP, "dcp300")
    elif(cpType==9):
        cp = DCPControl.DCPControl(cpIP, "dpm100")
    else:
        print("Error: invalid CP type")

def setUpCinemaProcessor():
    global cp, pState
    constructCinemaProcessorObject()
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
        return  'DCP100?'
    elif(code==7):
        return  'DCP200?'
    elif(code==8):
        return  'DCP300?'
    elif(code==9):
        return  'DMP100?'
    else:
        return 'UNKNOWN'

def main():
    global cp, pState, enc, encbtn
    pState = 0

    setUpDisplay()
    # Load settings from data.txt
    getData()
    if KEYPAD_EXISTS:
        km = keypad.KeyMatrix(row_pins=Config.ROW_PINS, column_pins=Config.COLUMN_PINS)
        KEYS = Config.KEYS
    encbtn = digitalio.DigitalInOut(ENCODER_BUTTON)
    encbtn.direction = digitalio.Direction.INPUT
    encbtn.pull = digitalio.Pull.UP
    enc = rotaryio.IncrementalEncoder(STEP, DIR)

    # Enter editIP by holding button on startup
    if(not encbtn.value):
        editIP()
    setupEthernet()
    setUpCinemaProcessor()
    enc.position = 0
    lastPosition = 0
    while 1==1:
        if dropped_requests > MAXDROPS:
            enc.position = 0
            lastPosition = 0
            setUpCinemaProcessor()
        if KEYPAD_EXISTS:
            event = km.events.get()
            if event:
                newmacro = Config.KEYS[event.key_number]
                if event.pressed and newmacro.isdigit():
                    cp.setmacro(newmacro)
        # If the position of the encoder changed, add/subtract it from the fader (modified by sensitivity)
        # Then adjust the position tracking value accordingly (used to be set back to zero, but
        # the sensitivity value would risk dropping half-ticks and the like.
        currentPosition = enc.position
        poitionChanges = currentPosition - lastPosition
        lastPosition = currentPosition
        volumeChange = math.floor(poitionChanges*SENSITIVITY)
        #print(position)
        if (volumeChange != 0):
            cp.addfader(volumeChange)

        #Update the display with the current value
        refreshDisplay()
        time.sleep(delay)
    # When the program is terminated, disconnect from the Cinema Processor and clear the displays.
    #cp.disconnect()

if __name__ == '__main__':
    main()

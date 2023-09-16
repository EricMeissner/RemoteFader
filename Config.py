# Configuration file, seldom needs to be changed.
import board

# Pico IP
#OWN_IP = (192, 168, 1, 111)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 0, 1)
DNS_SERVER = (8, 8, 8, 8)


# Cinema Processor IP
#CP_IP = '192.168.1.149'

# Polling/update delay in seconds
# A lower delay will make the the fader more responsive, BUT if it is too low
# the frequent requests to the Cinema Processor can be rejected, causing buggy responses.
POLLING_DELAY = 0.3

# Encoder Sensitivity
# We had an encoder that incremented twice for one click, so we added this so we could
# decrease the sensitivity to 0.5 for it.
SENSITIVITY = 1

# Encoder pins
DIR = board.GP2
STEP = board.GP3
# Encoder button
ENCODER_BUTTON = board.GP4

# I2C pins
SDA = board.GP0
SCL = board.GP1

# Ethernet pins
SPI1_SCK = board.GP18
SPI1_TX = board.GP19
SPI1_RX = board.GP16
SPI1_CSn = board.GP17
W5500_RSTn = board.GP20

# No clue how this works with the hardware, but the following code might help you find the correct address:
#if (i2c.try_lock()):
#    print("i2c.scan(): " + str(i2c.scan()))
#    i2c.unlock()
DEVICE_ADDRESS = 0x3c

DISPLAYWIDTH = 128
DISPLAYHEIGHT = 64

# Ports for Cinema Processors
# These shouldn't ever need to change
# DOLBYPORT = 61408       # port for Dolby CP_50 Cinema Processors
# CP650PORT = 61412
# JSDPORT = 10001         # port for JSD Cinema Processors

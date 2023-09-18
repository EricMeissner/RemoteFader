# Configuration file, seldom needs to be changed.
import board

# Pico IP
#OWN_IP = (192, 168, 1, 111)
SUBNET_MASK = (255, 255, 255, 0)
GATEWAY_ADDRESS = (192, 168, 0, 1)
DNS_SERVER = (8, 8, 8, 8)

# Polling/update delay in seconds
# A lower delay will make the the fader more responsive, BUT if it is too low
# the frequent requests to the Cinema Processor can be rejected, causing buggy responses.
POLLING_DELAY = 0.3
#POLLING_DELAY = 0.5

# Encoder Sensitivity
# We had an encoder that incremented twice for one click, so we added this so we could
# decrease the sensitivity to 0.5 for it.
SENSITIVITY = 1

# Encoder pins
DIR = board.GP2
STEP = board.GP3
# Encoder button
ENCODER_BUTTON = board.GP4

# Display Type options
#   1 = SSD1306     (Monochrome: W=128, H=64)
#   2 = ST7735R/S   (MultiColor: W=128, H=160)
DISPLAY_TYPE = 1

# I2C pins (If using SSD1306)
SDA = board.GP0
SCL = board.GP1
DEVICE_ADDRESS = 0x3c

# SPI stuff (If using ST7735R/S)
#SPI_CLOCK = board.GP10
#SPI_MOSI = board.GP11
#SPI_RESET = board.GP12
#SPI_CS = board.GP14     #Chip select
#SPI_DC = board.GP13     #Data command control

#DISPLAY2_WIDTH = 128 #This has only been an issue with ST7735 displays (type 2).
#DISPLAY2_HEIGHT = 160 #Height and width for SSD1306 (display type 1) are hardcoded.

# SSD1306 is monochrome and will therefore default to white text
#TEXT_COLOR = 0x32CD32       #Lime green
#TEXT_COLOR = 0xFF0000       #Red
#TEXT_COLOR = 0x808080       #Gray
#TEXT_COLOR = 0x0000FF       #Blue

#DISPLAY_COLOR = 0x32CD32    #Lime green

#HEADER_COLOR = 0xFF0000       #Red


# Ethernet pins
SPI1_SCK = board.GP18
SPI1_TX = board.GP19
SPI1_RX = board.GP16
SPI1_CSn = board.GP17
W5500_RSTn = board.GP20


# Key Matrix config
# This is for implementations with macro buttons.
# If you install a keypad, switch KEYPAD_EXISTS to True and check the row/column pins.
KEYPAD_EXISTS = False

# SSD1306 wiring
ROW_PINS = (board.GP6, board.GP7, board.GP8, board.GP9)
COLUMN_PINS = (board.GP10, board.GP11, board.GP12, board.GP13)

# ST7735R wiring
#ROW_PINS = (board.GP0, board.GP1, board.GP6, board.GP7)
#COLUMN_PINS = (board.GP8, board.GP9, board.GP28, board.GP27)

KEYS = (
    "1", "2", "3", "A",
    "4", "5", "6", "B",
    "7", "8", "9", "C",
    "*", "0", "#", "D"
)
#Do not use numeric keys for special functions as those are reserved for Format/input/macro numbers
#Do not mark multiple keys to the same function. I did not make the code to handle that sort of tomfoolery.
FORMAT_KEY = "A"
#If MUTE_KEY is not given or = False, there will be no mute function.
MUTE_KEY = "D"
UNMUTE_KEY = "C"

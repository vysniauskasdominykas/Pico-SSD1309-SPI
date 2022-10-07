import time
import machine
import framebuf

# Reference:
# https://www.hpinfotech.ro/SSD1309.pdf
# pages 27-34.

# Fundamental commands
SSD1309_SET_CONTRAST = 0x81
SSD1309_SET_ENTIRE_DISPLAY_RESUME_CONTENT = 0xA4
SSD1309_SET_ENTIRE_DISPLAY_IGNORE_CONTENT = 0xA5
SSD1309_SET_INVERSE_DISPLAY_OFF = 0xA6
SSD1309_SET_INVERSE_DISPLAY_ON = 0xA7
SSD1309_SET_DISPLAY_OFF = 0xAE
SSD1309_SET_DISPLAY_ON = 0xAF
SSD1309_SET_NO_OPERATION = 0xE3
SSD1309_SET_COMMAND_LOCK = 0xFD

# Scrolling commands
SSD1309_SET_HORIZONTAL_SCROLL_RIGHT = 0x26
SSD1309_SET_HORIZONTAL_SCROLL_LEFT = 0x27
SSD1309_SET_VERTICAL_AND_HORIZONTAL_SCROLL_RIGHT = 0x29
SSD1309_SET_VERTICAL_AND_HORIZONTAL_SCROLL_LEFT = 0x2A
SSD1309_SET_SCROLL_DEACTIVATE = 0x2E
SSD1309_SET_SCROLL_ACTIVATE = 0x2F
SSD1309_SET_VERTICAL_SCROLL_AREA = 0xA3
SSD1309_SET_HORIZONTAL_SCROLL_BY_COLUMN_RIGHT = 0x2C
SSD1309_SET_HORIZONTAL_SCROLL_BY_COLUMN_LEFT = 0x2D

# Addressing commands
SSD1309_SET_LOWER_COLUMN_START_ADDRESS_FOR_PAGE_ADDRESSING_MODE = 0x00
SSD1309_SET_HIGHER_COLUMN_START_ADDRESS_FOR_PAGE_ADDRESSING_MODE = 0x10
SSD1309_SET_MEMORY_ADDRESSING_MODE = 0x20
SSD1309_SET_COLUMN_ADDRESS = 0x21
SSD1309_SET_PAGE_ADDRESS = 0x22
SSD1309_SET_PAGE_START_ADDRESS_FOR_PAGE_ADDRESSING_MODE = 0xB0

# Hardware configuration commands
SSD1309_SET_DISPLAY_START_LINE = 0x40
SSD1309_SET_SEGMENT_REMAP_INVERSE = 0xA0
SSD1309_SET_SEGMENT_REMAP_NORMAL = 0xA1
SSD1309_SET_MULTIPLEX_RATIO = 0xA8
SSD1309_SET_COM_OUTPUT_SCAN_DIRECTION_INVERSE = 0xC0
SSD1309_SET_COM_OUTPUT_SCAN_DIRECTION_NORMAL = 0xC8
SSD1309_SET_DISPLAY_OFFSET = 0xD3
SSD1309_SET_COM_PINS_HARDWARE_CONFIGURATION = 0xDA
SSD1309_SET_GENERAL_PURPOSE_IO = 0xDC

# Timing & driving commands
SSD1309_SET_DISPLAY_CLOCK_DIVIDE_RATIO = 0xD5
SSD1309_SET_PRE_CHARGE_PERIOD = 0xD9
SSD1309_SET_VCOMH_DESELECT_LEVEL = 0xDB

class SSD1309SPI(framebuf.FrameBuffer):
    def __init__(self, display_width=128, display_height=64, gpio_chip_select=12, gpio_data_command=11, gpio_reset=10, gpio_serial_data=7, gpio_serial_clock=6):
        self.DISPLAY_WIDTH = display_width
        self.DISPLAY_HEIGHT = display_height
        
        self.serial_interface = machine.SPI(0, miso=None, mosi=machine.Pin(gpio_serial_data), sck=machine.Pin(gpio_serial_clock))
        
        self.frame_data = bytearray(self.DISPLAY_WIDTH * self.DISPLAY_HEIGHT // 8)
        super().__init__(self.frame_data, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT, framebuf.MONO_VLSB)
        #self.frame_buffer = framebuf.FrameBuffer(self.frame_data, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT, framebuf.MONO_VLSB)
        #self.frame_buffer.fill(0x00)
        
        self.pin_chip_select = machine.Pin(gpio_chip_select, mode=machine.Pin.OUT, value=1)
        self.pin_data_command = machine.Pin(gpio_data_command, mode=machine.Pin.OUT, value=0)
        self.pin_reset = machine.Pin(gpio_reset, mode=machine.Pin.OUT, value=1)
        
        self.reset_device()
        self.write_initialization_sequence()
        self.render()
        
    def write_initialization_sequence(self):
        self.write_command(SSD1309_SET_DISPLAY_OFF)
        
        self.write_command(SSD1309_SET_CONTRAST, value=0xFF)
        self.write_command(SSD1309_SET_PRE_CHARGE_PERIOD, value=0xF1)
        self.write_command(SSD1309_SET_VCOMH_DESELECT_LEVEL, value=0x40)
        
        self.write_command(SSD1309_SET_DISPLAY_START_LINE)
        self.write_command(SSD1309_SET_DISPLAY_OFFSET, value=0x00)
        self.write_command(SSD1309_SET_DISPLAY_CLOCK_DIVIDE_RATIO, value=0x80)
        
        if (self.DISPLAY_WIDTH != 64) and (self.DISPLAY_HEIGHT == 16 or self.DISPLAY_HEIGHT == 32):
            self.write_command(SSD1309_SET_COM_PINS_HARDWARE_CONFIGURATION, value=0x02)
        else:
            self.write_command(SSD1309_SET_COM_PINS_HARDWARE_CONFIGURATION, value=0x12)
            
        self.write_command(SSD1309_SET_SEGMENT_REMAP_NORMAL)
        self.write_command(SSD1309_SET_COM_OUTPUT_SCAN_DIRECTION_NORMAL)
        self.write_command(SSD1309_SET_MULTIPLEX_RATIO, value=self.DISPLAY_HEIGHT-1)
        self.write_command(SSD1309_SET_MEMORY_ADDRESSING_MODE, value=0x00)
        
        self.write_command(SSD1309_SET_ENTIRE_DISPLAY_RESUME_CONTENT);
        self.write_command(SSD1309_SET_INVERSE_DISPLAY_OFF);
        self.write_command(SSD1309_SET_DISPLAY_ON);
        
    def write_command(self, command, value=None):
        self.pin_data_command.value(0)
        self.pin_chip_select.value(0)
        self.serial_interface.write(bytearray([command]))
        self.pin_chip_select.value(1)
        
        if value != None:
            self.write_command(value)
        
    def write_buffer(self, buffer):
        self.pin_chip_select.value(1)
        self.pin_data_command.value(1)
        self.pin_chip_select.value(0)
        self.serial_interface.write(buffer)
        self.pin_chip_select.value(1)
        
    def render(self):
        self.write_command(SSD1309_SET_COLUMN_ADDRESS)
        self.write_command(0)
        self.write_command(self.DISPLAY_WIDTH - 1)
        
        self.write_command(SSD1309_SET_PAGE_ADDRESS)
        self.write_command(0)
        self.write_command(self.DISPLAY_HEIGHT // 8 - 1)

        self.write_buffer(self.frame_data)

    def clear(self):
        self.fill(0x00)
        self.render()
        
    def reset_device(self):
        self.pin_reset(1)
        time.sleep(1 / 1000)
        self.pin_reset(0)
        time.sleep(10 / 1000)
        self.pin_reset(1)
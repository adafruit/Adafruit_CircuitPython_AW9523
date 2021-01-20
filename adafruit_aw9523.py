# SPDX-FileCopyrightText: Copyright (c) 2021 ladyada for Adafruit
#
# SPDX-License-Identifier: MIT
"""
`adafruit_aw9523`
================================================================================

Python library for AW9523 GPIO expander and LED driver


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* Adafruit AW9523 Breakout https://www.adafruit.com/product/4886

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import time
import struct
import adafruit_bus_device.i2c_device as i2c_device
from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bit import RWBit
from micropython import const

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AW9523.git"

_AW9523_DEFAULT_ADDR = const(0x58)
_AW9523_REG_CHIPID = const(0x10)     # Register for hardcode chip ID
_AW9523_REG_SOFTRESET = const(0x7F)  # Register for soft resetting
_AW9523_REG_INPUT0 = const(0x00)     # Register for reading input values
_AW9523_REG_OUTPUT0 = const(0x02)    # Register for writing output values
_AW9523_REG_CONFIG0 = const(0x04)    # Register for configuring direction
_AW9523_REG_INTENABLE0 = const(0x06) # Register for enabling interrupt
_AW9523_REG_GCR = const(0x11)        # Register for general configuration
_AW9523_REG_LEDMODE = const(0x12)    # Register for configuring const current


class AW9523:
    
    _chip_id = ROUnaryStruct(_AW9523_REG_CHIPID, "<B")
    _reset_reg = UnaryStruct(_AW9523_REG_SOFTRESET, "<B")

    # Set all 16 gpio outputs
    outputs = UnaryStruct(_AW9523_REG_OUTPUT0, "<H")
    # Read all 16 gpio inputs
    inputs = UnaryStruct(_AW9523_REG_INPUT0, "<H")
    # Set all 16 gpio interrupt enable
    _interrupt_enables = UnaryStruct(_AW9523_REG_INTENABLE0, "<H")
    # Set all 16 gpio directions
    _directions = UnaryStruct(_AW9523_REG_CONFIG0, "<H")
    # Set all 16 gpio LED modes
    _LED_modes = UnaryStruct(_AW9523_REG_LEDMODE, "<H")

    # Whether port 0 is push-pull
    port0_push_pull = RWBit(_AW9523_REG_GCR, 4)
    

    def __init__(self, i2c_bus, address=_AW9523_DEFAULT_ADDR, reset=True):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buffer = bytearray(2)     
        if self._chip_id != 0x23:
            raise AttributeError("Cannot find a AW9523")
        if reset:
            self.reset()
            self.port0_push_pull = True # pushpull output
            self.interrupt_enables = 0x0000 # no IRQ
            self.directions = 0x0000 # all inputs!

    def reset(self):
        self._reset_reg = 0

    def set_constant_current(self, pin, value):
        # See Table 13. 256 step dimming control register
        if 0 <= pin <= 7:
            self._buffer[0] = 0x24 + pin
        elif 8 <= pin <= 11:
            self._buffer[0] = 0x20 + pin - 8
        elif 12 <= pin <= 15:
            self._buffer[0] = 0x2C + pin - 12
        else:
            raise ValueError("Pin must be 0 to 15")

        # set value
        if not (0 <= value <= 255):
            raise ValueError("Value must be 0 to 255")
        self._buffer[1] = value
        with self.i2c_device as i2c:
            i2c.write(self._buffer)

    @property
    def interrupt_enables(self):
        return ~self._interrupt_enables & 0xFFFF

    @interrupt_enables.setter
    def interrupt_enables(self, enables):
       self._interrupt_enables = ~enables & 0xFFFF

    @property
    def directions(self):
        return ~self._directions & 0xFFFF

    @directions.setter
    def directions(self, dirs):
       self._directions = ((~dirs) & 0xFFFF)

    @property
    def LED_modes(self):
        return ~self._LED_modes & 0xFFFF

    @LED_modes.setter
    def LED_modes(self, modes):
       self._LED_modes = ~modes & 0xFFFF

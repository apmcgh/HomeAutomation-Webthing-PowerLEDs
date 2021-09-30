# check for TODO
"""
Module:     webthing_dimmable_LED_strip.py

Purpose:
    Webthing to control a non-addressable LED strip.

    A webthing is a set of objects that present a standardised web interface to
    improve inter-operability of "Internet of Things" devices.

    The present webthing manages the lighting of LED strips that are controlled
    through power.

===============================================================================
Author:     Alain Culos
            programming-electronics@asoundmove.net

Bio:        I love programming (pro), I love data (pro), I enjoy electronics as
            a hobby.
            I have worked on small and large software projects in various
            industries: Defense (distributed systems, real-time, several
            seconds), Air Traffic Control (mainframes, real-time, sub-second),
            FinTech (software as a service, real-time, 10-100 milliseconds),
            Avionics testing (embedded, milliseconds) and Banking (various
            credit decision platforms, back office).
            Now building up my python credentials (learning, practice,
            sharing and giving back to the community).

Module history:
    2020-08-xx: proof of concept: electronics, driving the electronics with
                python on a Pi4
    2020-09-18: requirements specification and project documentation (the text
                below)
    2020-09-23: start development of the webthing - getting the basics of
                webthing to work
    2020-09-24: webthing works with all POC functionality and a bit more:
                Switching on and off or setting channels cleverly switches the
                relay on and off appropriately (i.e. depending whether all
                channels are 0).
                Also checking that values are only set for channels that belong
                to the control.
    2020-10-04: V1.0
                webthing works with all basic functionality and loading
                calibration curves from files.

                Standard properties implemented:
                    on
                         '@type':       'OnOffProperty',
                    brightness
                         '@type':       'BrightnessProperty',
                    colour
                         '@type':       'ColorProperty',

                Non-standard properties implemented:
                     channel_brightness
                         '@type':       'ChannelBrightnessProperty',
                     channel_curve
                         '@type':       'ChannelCurveProperty',

                Other key developments:
                    load_calibration (and the Compute-LED-calibration.py that
                    feeds it, based on the output of multiple runs, one per
                    channel, of PWM_and_MOSFET_calibration.py)
                    Some manual fine tuning of the calibration happens in
                    Compute-LED-calibration.py
                    We could have integrated this step in here, but I did not
                    want to have to run webthing with pandas and I did not want
                    to introduce an extra delay at start-up.

    2020-10-07: Improved inline documentation
    2020-10-16: Completed wiring documentation
    2020-11-23: After much testing on a gateway add-on, it turns out that using
                the id field to store useful data is lost on clients of the
                gateway.
                New solution: implement a "location" property.
    2021-02-12: Adding BME280 for temperature, humidity and pressure monitoring
                Hardware addition, early software development of the sensor
                functions, my beginnings at using asyncio.

TODO, problems to solve:
    1/ SW: think about how to terminate the execution of a pattern mid-way
    2/ SW: exception handling
    3/ SW: test automation
    4/ SW: Consider https://github.com/hidaris/thingtalk for asyncio programming

===============================================================================
Future:
    This is a hobby project to control LED lights in my home. There may be new
    functions to develop to make the lights easier or more fun to use.

    As this is a hobby project, it will remain perfect in its imperfection:
    sufficiently good to do the job rather efficiently. Of course it is not
    production grade, it does not need to be.

Copyright:
    Alain P.M. Culos 2020-2021, all rights reserved.

Licence:
    You shall not use this code as part of a commercial activity without
    reaching an explicit written commercial agreement with the author for
    exclusive or non exclusive commercial use rights. Commercial activity
    includes any activity that facilitates directly or indirectly another
    commercial activity even if this software is not used in a commercial
    product per se.
    This includes private education, R&D even if indirectly linked to profit...

    You may use the present code and text in part or whole free of charge for
    any non-commercial activity.
    This includes state sponsored education, volunteer run organisations, not
    for profit organisations, and of course hobbyists, open source projects.
    You must acknowledge the author, include and respect the terms of this
    licence.

Disclaimer:
    Use at your own risk.

    The author makes no claim as to suitability for purpose. Any consequence is
    beyond my control and entirely your responsability. Before you use this you
    should have the relevant knowledge to handle electronics and electrical
    power. The author is not an electrician or an electronics specialist so he
    cannot provide advice. You should also undesrtand the relationships between
    software and hardware as overheating electronics can cause fires and bare
    wires can cause electrocution.

    The purpose of sharing the present file is for self learning and exchange
    with like-minded people (curious, tinkerer, maker, DIYer).

===============================================================================
Low level functions:
    Raspberry Pi    -> power switch to power supply to feed the LED strip(s)
                    :: ON, OFF

    Raspberry Pi    -> PWM          to control the LED strip(s) intensity
                    :: SET <CH#> <level>

    Raspberry Pi    -> Raspberry Pi to control the LED strip(s) intensity
                    :: CONFIGURE <CH#> <translation>

    PWM             -> MOS FET      to control the LED strip(s) intensity
    Power supply    -> MOS FET      to feed the LED strip(s)
    MOS FET         -> LED strip(s) to feed and control the LED strip(s)
                       intensity

    Weather         -> Temperature, Humidity & Pressure sensor

    Note:
            ON          Dimmable_LED_strip_webthing.OnOff
            OFF         Dimmable_LED_strip_webthing.OnOff
            SET         Dimmable_LED_strip_webthing.channel_brightness
            CONFIGURE   # done at initialisation of
                          "Dimmable_LED_strip_channels"

Webthing capabilities (what this module provides):
    Switch on:          ON if OFF, SET
                        Use last setting or predefined setting depending on
                        configuration

    Switch off:         OFF, SET to level 0
                        TODO: Remember pointer in current pattern (pause yield
                        loop?)

    Configure curve:    CONFIGURE
                        Set the translation curve for light intensity
                        (intended) to PWM ratio Note: on the MOS FET board each
                        channel behaves quite differently, at the same time,
                        the LED colours seem to also behave differently: for
                        both small variances in input can yield large
                        differences in light output but not at the same points
                        in the curve.
                        See "PWM_and_MOSFET_calibration.py" and
                        "Compute-LED-calibration.py" for details on how to
                        perform a semi-automatic calibration.
                        Bear in mind that potentially each MOSFET / LED strip
                        combination potentially requires different calibration
                        data.
                        We could imagine a self-calibration set-up with an ADC
                        on the MOS FET output, but that also poses the question
                        of calibration of the ADC channels at least relative to
                        one another. Plus since calibration is probably only
                        required once, the ADC set-up should be a removable
                        "plug-in" (literally).

    Set brightness:     ON if level > 0, SET, OFF if level = 0
                        Dimmable_LED_strip_webthing.brightness

    Set colour:         ON if level > 0, SET, OFF if level = 0
                        Dimmable_LED_strip_webthing.channel_brightness
                        Dimmable_LED_strip_webthing.colour

    Image pattern:      ON if OFF, SET, OFF if last level = 0, if not looping
                        TODO - not yet implemented

    Array pattern:      ON if OFF, SET, OFF if last level = 0, if not looping
                        TODO - not yet implemented

    Function pattern:   ON if OFF, SET, OFF if last level = 0, if not looping
                        TODO - not yet implemented

Physical diagram:
                 +---------+
                 | Weather |
                 +---------+
                      ^
    +----+    +-----+ |  +-----+       +---------+                +------------+
    | 5V |--->| rPi |-+->| PWM |-4 ch->| MOS FET |-> 4 channels ->| LED strips |
    +----+    +-----+    +-----+       +---------+                +------------+
                  |                         ^
                  v       +---------------+ |
    +-------+  +-------+  |  Transformer  | |
    | Mains |->| Relay |->| Mains --> LED |-+
    +-------+  +-------+  | strip voltage |
                          +---------------+

    Notes:
    Depending on the chosen MOS FET board, it is possible to accommodate a wide
    variety of voltages.

Wiring:
    Mains - Relay
        Mains: Live, Brown  -> Relay: COM (terminal block, middle)

    Mains - 5V transformer
        Mains: Live, Brown  -> 5V: ACL
        Mains: Neutral, Blue-> 5V: ACN

    Mains - 12V transformer
        Mains: Neutral, Blue-> 12V: ACN

    5V - Pi
        5V: +5V             -> Pi: Pin02, 5V (or USB power cable, red wire)
        5V: GND, 0V         -> Pi: Pin06, GND (or USB power cable, black wire)
            Note: beware to only connect the 5V supply to one place on the Pi.
            It can be via the PWR USB input or via a 5V pin, but not both.

    5V - Relay
        5V: +5V             -> Relay: VCC (pin nearest green LED)
        5V: GND, 0V         -> Relay: GND (middle pin)

    5V - PWM: I2C bus + 5V
        5V: +5V             -> PCA9685: Long side, Power block (2 screws), V+
                               (left, if at the top)
        5V: GND, 0V         -> PCA9685: Long side, Power block (2 screws), GND

    Relay - 12V transformer
        Relay: NO TB, left  -> 12V: ACL

    12V - MOS FET
        12V: DC -           -> MOS FET: DC -
        12V: DC +           -> MOS FET: DC +

    Pi - Relay: GPIO + resistor
        Pi: GPIO23, Pin16   -> one side of 10k Resistor
        10kR: other side    -> Relay: IN (pin nearest red LED)

    Pi - PWM: I2C bus + 5V
        Pi: +3.3V, Pin01    -> PCA9685: VCC, Short side, Pin5
                               (2nd from bottom, if on the left)
        Pi: SDA, Pin03      -> PCA9685: SDA, Short side, Pin4
        Pi: SCL, Pin05      -> PCA9685: SCL, Short side, Pin3
        Pi: GND, Pin09      -> PCA9685: GND, Short side, Pin1 (top)

        Note: it is safe to power PWMs that control a MOS FET from the
        Raspberry Pi Zero 5V, but it would not be safe to do so to control
        motors.
        However to keep wring neater, and as the power supply is available in
        the same vicinity as the Pi, I will power everything directly from the
        power supply.

    Pi - Weather: I2C bus
        Pi: +3.3V, Pin01    -> BME280: VIN
        Pi: SDA, Pin03      -> BME280: SDA
        Pi: SCL, Pin05      -> BME280: SCL
        Pi: GND, Pin09      -> BME280: GND

    PWM - MOS FET
        PWM: PWM 0          -> MOS FET: PWM 1
        PWM: PWM 1          -> MOS FET: PWM 2
        PWM: PWM 2          -> MOS FET: PWM 3
        PWM: PWM 3          -> MOS FET: PWM 4

        PWM: GND 0          -> MOS FET: GND 1
        PWM: GND 1          -> MOS FET: GND 2
        PWM: GND 2          -> MOS FET: GND 3
        PWM: GND 3          -> MOS FET: GND 4

    MOS FET - LED
        MOS FET: OUT 1 -    -> LED RGB: Red     (Channel 0)
        MOS FET: OUT 2 -    -> LED RGB: Green   (Channel 1)
        MOS FET: OUT 3 -    -> LED White: Black (Channel 2)
        MOS FET: OUT 4 -    -> LED RGB: Blue    (Channel 3)

        MOS FET: OUT 1 +    -> LED RGB: Black
        MOS FET: OUT 2 +    -> LED RGB: Black
        MOS FET: OUT 3 +    -> LED White: Red
        MOS FET: OUT 4 +    -> LED RGB: Black

Implementation detail:
    The Raspberry Pi communicates with the PWM board via the i2c bus.
    The Raspberry Pi controls the relay via a GPIO (out of course) + 10 kOhms
    resistor.
    The PWM outputs each control a MOS FET input.

Implementation tested:
    POC developped on Raspberry Pi4

Target implementation (all these can be changed to suit your needs):
    Raspberry Pi0
        Purpose:        Where the logic happens: where the (python) "webthing"
                        program lives.
                        The reason for the Raspberry Pi0 as opposed to Arduino,
                        is the ease of development
                        The reasons for the Raspberry Pi0 as opposed to Pi2, 3
                        or 4 are cost and small footprint
                        The reason for Pi0 plain as opposed to wireless are the
                        potential instability of wireless
                        Network via Ethernet USB dongle as well as cost
        Buy:            https://thepihut.com/products/raspberry-pi-zero
        Specification:  https://www.raspberrypi.org/products/raspberry-pi-zero/
        Power:          https://www.circuits.dk/everything-about-raspberry-gpio/
                        Max 50mA on 3.3V pins
                        Max 16mA on any GPIO pin (not all at oncei: max 50mA total)
                        PSU-100mA on 5V supply (including USB)

                        GPIOs really available:
                             4  (7),  5 (29),  6 (31),
                            12 (32), 13 (33),
                            16 (36), 17 (11),
                            20 (38), 21 (40), 22 (15), 23 (16),
                            24 (18), 25 (22), 26 (37), 27 (13)


                                       3V3  (1) (2)  5V    
                           I2C SDA   GPIO2  (3) (4)  5V    
                           I2C SCL   GPIO3  (5) (6)  GND   
                                     GPIO4  (7) (8)  GPIO14  Serial
                                       GND  (9) (10) GPIO15  Serial
                                    GPIO17 (11) (12) GPIO18  HW PWM
                                    GPIO27 (13) (14) GND   
                                    GPIO22 (15) (16) GPIO23
                                       3V3 (17) (18) GPIO24
                           SPI      GPIO10 (19) (20) GND   
                           SPI       GPIO9 (21) (22) GPIO25
                           SPI      GPIO11 (23) (24) GPIO8   SPI
                                       GND (25) (26) GPIO7   SPI
                           Reserved  GPIO0 (27) (28) GPIO1   Reserved
                                     GPIO5 (29) (30) GND   
                                     GPIO6 (31) (32) GPIO12
                                    GPIO13 (33) (34) GND   
                           HW PWM   GPIO19 (35) (36) GPIO16
                                    GPIO26 (37) (38) GPIO20
                                       GND (39) (40) GPIO21


    PWM
        Purpose:        The Raspberry Pi only has 2 hardware PWMs, one of which
                        cannot be used if the I2C bus is being used. Software
                        PWM is too unreliable.
                        To control 3 or more channels, an extra board is
                        required, with a key advantage that the external PWM
                        frees up Raspberry Pi resources.
                        This board offers 16 PWM channels via the I2C bus.
        Buy:            https://www.aliexpress.com/item/4000468996665.html
        Specification:  https://cdn-shop.adafruit.com/datasheets/PCA9685.pdf
        Notes:          16 channels, of which we use 4, but we could use up to
                        62 of these boards as they can be configured with
                        soldering any of 6 hardware pins. That could command
                        992 channels!
                        To power this many PWMs, a beefier 5V supply might be
                        required, and if all channels drove power LEDs, many
                        and stronger transformers would be required to supply
                        the load.
        How-to:         https://learn.adafruit.com/16-channel-pwm-servo-driver/python-circuitpython
                        https://circuitpython.readthedocs.io/projects/pca9685/en/latest/api.html
        Power:          According to the datasheet for this board, the I2C bus
                        is capable of drawing 30mA, but it is not clear how
                        much it actually draws. Another source was quoting 30
                        micro Amps!
                        The outputs are powered by the 5V supply.

    MOS FET F5305S
        Purpose:        Modulate (dim) and drive 12V power to the LED strips
        Buy:            https://www.aliexpress.com/item/33015020793.html
        Specification:  see above
        Notes:          4 channels, add more boards to drive more channels.
        How-to:         Plug PWM outputs to board inputs,
                        Plug reference voltage,
                        Plug LED power wires to be driven.
        Power:          5mA per input (driven by PWM 5V)
                        5A max output (20A with heat sinks)

    Relay
        Purpose:        Switch off the 12V power supply when not required (save
                        residual current draw when lights are off)
        Buy:            https://www.aliexpress.com/item/32909882481.html
        How-to:         https://www.instructables.com/id/5V-Relay-Module-Mod-to-Work-With-Raspberry-Pi/
        Notes:          No need to go out to town on the mod, simply inserting
                        a 10kOhm resistor between the Pi GPIO and the "in" pin
                        of the relay works for me.
                        GPIO = 0, means COM connects to NC and disconnects from NO
                        GPIO = 1, means COM connects to NO and disconnects from NC

    Weather sensor

    Micro SD card
        Buy:            Not anywhere! Watch the quality, some cheap ones do not
                        work well for very long on the Raspberry Pi.
        Specification:  Class 10
        How-to:
                Part 1 - prepare the SD card - this requires a different
                        computer, instructions here for Linux
                        # Note: this prepares a headless system
                        apt install rpi-imager # OR
                        snap install rpi-imager
                        rpi-imager
                        # Select Raspberry OS 32 bit lite, select the correct
                        # SD card, write to it

                        # Remove and re-insert the SD card
                        # Replace the "*" below with the correct path
                        touch /media/*/boot/ssh
                        nano /media/*/rootfs/etc/dhcpcd.conf
                        # Set static address and routing (use your text editor
                        # of choice, personally I prefer vim but nano seems
                        # standard in any published instructions)

                        nano /media/*/rootfs/etc/hostname
                        umount boot; umount rootfs
                        ssh pi@<ip>

                Part 2 - connect the Raspberry Pi zero
                        Insert micro SD card,
                        Connect micro USB Ethernet dongle & Ethernet cable (or
                        go wireless, but you are on your own),
                        Connect power

                        Note: if the green LED near the micro USB socket marked
                        "PWR IN" blinks 7 times, it means the SD card is
                        corrupt. This can happen after a reboot with a bad
                        card, if it happens twice with the same card, discard
                        it and use a different card.

                Part 3 - configure the Raspberry Pi zero
                        passwd
                        # change default password to something personal

                        apt update
                        # update package database

                        apt upgrade
                        # upgrade packages already installed that need updating

                        apt install screen vim
                        # some useful tools

                        apt install python3-pip
                        # essential tool

                        raspi-configi
                        # Interfacing options, enable i2c, enable remote gpio,
                        # enable serial

                        mkdir -p Documents/GPIO-programming
                        cd !:2
                        python3 -m pip install RPi.GPIO
                        python3 -m pip install Adafruit-GPIO
                        # This may be unnecessary, could included i the
                        # following update

                        python3 -m pip install adafruit-circuitpython-adafruitio
                        python3 -m pip install adafruit-circuitpython-pca9685
                        python3 -m pip install adafruit-circuitpython-bme280

                        python3 -m pip install adafruit-circuitpython-ads1x15
                        # useful for calibration, if you have the ADS1115

                        python3 -m pip install webthing

                Part 4 - develop/install/test/customise this program
                        Development:
                            A lot of help got from the following links (and
                            many others):
                            https://github.com/mozilla-iot/webthing-python/tree/master/webthing
                            https://github.com/WebThingsIO/webthing-python/blob/master/webthing/thing.py
                            https://github.com/WebThingsIO/webthing-python/blob/master/webthing/property.py
                            https://github.com/WebThingsIO/webthing-python/blob/master/webthing/value.py
                            https://github.com/WebThingsIO/webthing-python/blob/5b779b5d3e545c93d636a0f6fac1582512cba62d/example/multiple-things.py
                            https://iot.mozilla.org/wot/
                        Testing:
                            Although I did not document testing, I covered a
                            lot of test cases (unit, integration, user
                            stories).
                            Obviously I may have missed some cases, please
                            share your observations.

                Part 5 - backup the SD card
                        shutdown -h 0
                        # Power off the Raspberry Pi Zero
                        # Remove the SD card and place in a different computer
                        # Take an image copy of this SD card so it can be
                        # easily restored in the event of a failure
                        # In linux (check which device the card comes under)
                        dd if=/dev/sdc of=/Your/Backup/Directory/BackupNameForYourSDCard.img
                        # I suggest the backup name should contain a date and
                        # the hostname or IP address of your Pi0

                        # Put the SD card in the Pi0
                        # Power-up the Pi
                        # If it does not work, you most likely have a low
                        # quality SD card

                Part 6 - use the gateway
                        On a Raspberry Pi 4, install the arm deb package from
                        (note the Gateway does not work on Pi0):
                        https://github.com/WebThingsIO/gateway/releases

                        Do this rather than the image if you want to retain
                        full control of your Raspberry Pi 4, for example
                        because you use it for other purposes.

                        The installation enables a service which gets started
                        at boot.

    Ethernet USB dongle
        Buy:            https://www.aliexpress.com/item/32970621991.html
        How-to:         Plug & play - need to configure the network (static
                        address is probably best, makes it easier to ssh into
                        the right box)

    Dupont line
        Buy:            https://www.aliexpress.com/item/4000192140351.html
        Specification:  Your requirements may vary
        Notes:          This is mostly useful for prototyping

    Transformer / Power supply - 5V
        Buy:            https://www.aliexpress.com/item/4000094353564.html
        Notes:          Needs to cater for the Raspberry Pi, PWM board, MOS
                        FET, Relay
                        All well under 2A (in fact well under 1A), but let's
                        build in some space for growth, a 2A, 5V power supply
                        is inexpensive.
        How-to:         See wiring above - always wire with the power off.

    Transformer / Power supply - 12V
        Buy:            https://www.aliexpress.com/item/4000094353564.html
        Notes:          Needs to cater for the LED strips.
                        In my scenario, this should have been about 3 or 4A,
                        but measuring the current consumption (with a
                        multimeter) shows that when all four PWMs are fully on,
                        with my two strips (one RGB, one White), the current
                        used is only about 2A.
                        Again, allowing for a bit of growth, let's take a 4A
                        power supply.
        How-to:         See wiring above - always wire with the power off.

    RGB LED Strip
        Buy:            https://www.aliexpress.com/item/32809840774.html
        Specification:  RGB + 5050 120led IP21
        How-to:         See wiring above - always wire with the power off.

    White LED Strip
        Buy:            https://www.amazon.co.uk/gp/product/B00C6SHZSE/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1
        Description:    Waterproof Cool White DC 12V 5M 3528 SMD 300 Leds LED
                        Strips Strip Light
        How-to:         See wiring above - always wire with the power off.

"""

# Using https://iot.mozilla.org/framework/ as a template
# Not sure why or how, but `division` is used by `webthing`
# Webthing enables exposing a standard interface for controlling Internet of
# Things objects.
from __future__ import division
from webthing import (Action, Event, Property, MultipleThings, Thing, Value,
                      WebThingServer)
import logging  # First port of call for debugging
import time
import math
import asyncio
#import uuid     # TODO: currently unused (came from the example webthing)

import RPi.GPIO as GPIO # To control the 12V relay
import board            # To use the I2C bus
import busio            # To use the I2C bus

# PWM - PCA9685
# extension board that can produce up to 16 HW PWMs 40 Hz to 1600 Hz.
from adafruit_pca9685 import PCA9685
import adafruit_bme280

import pickle
import numpy


#TODO: develop an auto-off timer function - which would trigger this event
"""
class AutoOffEvent(Event):
    def __init__(self, thing, data):
        Event.__init__(self, thing, 'auto-off', data=data)
"""


#TODO: develop functions to produce smooth intensity transitions when switchiing lights on and off, or changing levels
"""
class FadeAction(Action):

    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, 'fade', input_=input_)

    def perform_action(self):
        time.sleep(self.input['duration'] / 1000)
        self.thing.set_property('brightness', self.input['brightness'])
        self.thing.add_event(OverheatedEvent(self.thing, 102))
"""


def scale(value, max_value, name = "value"):
    """
    """

    v = 0 if value <= 0 else max_value if value >= 1 else int(value * max_value)
    logging.debug(f"{name}={value:0.3f} x {max_value} -> scaled {name}={v}")
    return v


class Dimmable_LED_strip_channels():
    """
    This class manages the hardware interface: GPIOs and I2C communications for
    control of the PWM channels.
    The reason for separating this layer from the webthing is that we can
    define muultiple instances of Dimmable_LED_strip_webthing that refer to
    common channels.
    This allows to have the best of both worlds: one can manage 4 channels as
    one entity, or split them in 3+1 channels for example, and change between
    the two at any time.
    """

    def __init__(self, on_off_channel, i2c_bus, frequency, channels, channel_curves):
        """
        on_off_channel      # The GPIO output pin that controls the relay to
                            # the transformer
        i2c_bus             # The I2C bus object - passed as a parameter to
                            # avoid multiple declarations
        frequency           # The frequency at which we will operate the PWM
                            # and therefore the lights
                            # Note that frequency and channel_curves are
                            # inter-dependant.
        channels            # The PWM channels to use for all lights
        channel_curves      # These curves attempt to correct the non linearity
                            # between the PWM control value and the voltage
                            # (TODO: or power?) output.
                            # The curves are the result of a "manual"
                            # calibration process.
                            # See module PWM_and_MOSFET_calibration.py for
                            # details.

        channels = {        # A dictionary that associates channel names with
         "channel name":    # Can be anything, it is a label, this will be the
                            # key to colour data
         channel_number,    # Channel on the PWM board, this corresponds to a
                            # given pair of wires
         ...
        }

        channel_curves = {  # A dictionary that associates channel names with
                            # curves.
         "channel name":    # Key to colour data, same same as in the
                            # `channels` parameter
          {                 # The curve: a dictionary that associates keys with
                            # values.
            brightness:     # The key is a number from 0 to 1 which is the
                            # intended brightness of the channel to which
                            # corresponds:
            PWM_duty_cycle, # The value which is also a number from 0 to 1 but
                            # represents the PWM duty cycle that needs to be
                            # set to achieve the wanted brightness.
            ...
          }
        }
        """

        self.on_off_channel = on_off_channel
        self.channels       = channels
        self.channel_curves = channel_curves

        # set-up communication with the PWM board
        self.PWM_board      = PCA9685(i2c_bus)

        self.things         = {}
        self.all_things     = []
        self.value          = {}
        self.last_on_value  = {}
        self.default_value  = {}

        self.PWM_board.frequency = frequency

    def register_thing_with_LED_strip_channels(self, thing):
        """
        As this module provides for multiple ways to access LED channels, we
        need to keep tabs as to which "webthing" object refers to which
        channel, so that we are able to notify the relevant subscribers of
        state changes.
        """

        # First call: set-up the GPIO pin to be an output (it controls the
        # relay to the transformer) as this pin is shared by all channels, it
        # only makes sense to initialise it once. set it to OFF (no power)
        if len(self.all_things) == 0:
            GPIO.setup(self.on_off_channel, GPIO.OUT)
            GPIO.output(self.on_off_channel, False)

        # Register all "webthing"s that use any channel
        if not thing in self.all_things:
            self.all_things.append(thing)
            logging.info(
                'Dimmable_LED_strip_channels: '
                f'len={len(self.all_things)}: {self.all_things}.'
            )

        # For each channel, register all "webthing"s that use this channel
        for c in thing.channels:
            if not c in self.things:
                self.things[c] = [thing, ]
                logging.info(
                    'Dimmable_LED_strip_channels: '
                    f'Setting "{thing.title}" to channel {c}.'
                )
            else:
                self.things[c].append(thing)
                logging.info(
                    'Dimmable_LED_strip_channels: '
                    f'Adding "{thing.title}" to channel {c}.'
                )

            # initialise channel current value
            self.value[c]           = 0.0

            # initialise channel value when "webthing" was last ON
            self.last_on_value[c]   = 0.0

            # initialise channel default value: if last_on are all 0, use default
            self.default_value[c]   = 0.2

            logging.info(
                'Dimmable_LED_strip_channels: '
                f'Associated "{c}" channel & '
                f'on/off pin {self.on_off_channel} '
                f'with {", ".join((f"""{t.title}""" for t in self.things[c]))}.'
            )

    def OnOff(self, thing, value):
        """
        Switch channel on (value is True) or off (value is False)
        If all channels are at 0 (not just those of the current "webthing"
        (thing)), then turn off the relay.
        If at least one channel is non zero, then turn on the relay.
        """

        logging.info(
            'Dimmable_LED_strip_channels: '
            f'{self.on_off_channel} to {"ON" if value else "OFF"}.'
        )

        if value:
            # Switch LEDs ON
            # Notify subscribers of all webthings that use any channel of the
            # change to the "on" property.
            v = {k: self.last_on_value[k]  for k in thing.channels}

            if sum(v.values()) > 0:
                self.channel_brightness(thing, v)
            else:
                self.channel_brightness(
                    thing,
                    {k: self.default_value[k]  for k in thing.channels}
                )

            for thing2 in self.all_things:
                t2v = [self.value[k]  for k in thing2.channels]
                logging.info(f'Dimmable_LED_strip_channels: {thing2.title}: {t2v}.')

                if sum(t2v) > 0:
                    logging.info(f'Dimmable_LED_strip_channels: {thing2.title} to "ON".')
                    thing2.properties["on"].value.notify_of_external_update(True)
                else:
                    logging.info(f'Dimmable_LED_strip_channels: {thing2.title} to "OFF".')
                    thing2.properties["on"].value.notify_of_external_update(False)

                thing2.properties["brightness"].value.\
                    notify_of_external_update(scale(max(t2v), 100, "brightness"))

        else:
            # Switch LEDs OFF
            # Notifications are handled by `reset`
            self.reset(thing, {k: 0  for k in thing.channels})

    def brightness(self, thing, value):
        """
        """

        logging.info(f'Dimmable_LED_strip_channels: {self.channels} brightness to {value}.')

        values = {k: self.value[k]  for k in thing.channels}
        if sum(values.values()) == 0:
            values = {k: self.last_on_value[k]  for k in thing.channels}
            if sum(values.values()) == 0:
                values = {k: self.default_value[k]  for k in thing.channels}

        scale = value / (100 * max(values.values()))
        self.channel_brightness(thing, {k: v*scale  for k, v in values.items()})

    def colour(self, thing, value):
        """
        """

        logging.info(f'Dimmable_LED_strip_channels: {self.channels} colour to {value} for {thing.title}, {thing.colour_type}.')

        if   thing.colour_type == "RGB":
            self.channel_brightness(
                thing, 
                {"Red":     int(value[1:3], 16) / 255.0,
                 "Green":   int(value[3:5], 16) / 255.0,
                 "Blue":    int(value[5:7], 16) / 255.0,
                }
            )

        elif thing.colour_type == "RGBW":
            r = int(value[1:3], 16) / 255.0
            g = int(value[3:5], 16) / 255.0
            b = int(value[5:7], 16) / 255.0
            w = min((r, g, b))
            W = w * (1 - max((r, g, b, 0.0001)))

            self.channel_brightness(
                thing, 
                {"Red":     r - W,
                 "Green":   g - W,
                 "Blue":    b - W,
                 "White":   w,
                }
            )

        elif thing.colour_type == "W":
            r = int(value[1:3], 16) / 255.0
            g = int(value[3:5], 16) / 255.0
            b = int(value[5:7], 16) / 255.0

            self.channel_brightness(thing, {"White": numpy.mean((r, g, b))})

    @staticmethod
    def __find_segment(value, curve):
        """
        Find between which two keys `value` lies in the `curve` - which is a list of segments
        This is the intended brightness.
        Return the segment ends (key, value) pairs.
        """

        pchannel_brightness, pPWM_duty_cycle = 0, 0
        for channel_brightness in curve:
            if value <= channel_brightness:
                return [[pchannel_brightness, pPWM_duty_cycle], [channel_brightness, curve[channel_brightness]]]
            pchannel_brightness, pPWM_duty_cycle = channel_brightness, curve[channel_brightness]
        return [[pchannel_brightness, pPWM_duty_cycle], [1, 1]]

    @staticmethod
    def __apply_curve(value, curve):
        """
        Calculate the PWM duty cycle we need to set based on the intended brightness
        Return that value
        """

        if type(curve) is int:
            return value * (1 - curve) + curve
        else:
            ((channel_brightness1, PWM_duty_cycle1), (channel_brightness2, PWM_duty_cycle2)) =  \
                Dimmable_LED_strip_channels.__find_segment(value, curve)

            return PWM_duty_cycle1 + (value - channel_brightness1) *                            \
                                     (PWM_duty_cycle2 - PWM_duty_cycle1) /                      \
                                     (channel_brightness2 - channel_brightness1)

    def __rectified_channel(self, value, channel_name):
        """
        Calculate, scale and cap the PWM duty cycle we need to set based on the intended brightness
        Return the scaled and capped value (as it must conform to the ADS device specification)
        """
        return scale(self.__apply_curve(value, self.channel_curves[channel_name]), 0xfffe, "PWM " + channel_name)

    def reset(self, thing, values):
        """
        Set channel values to zero, remember last ON values, but only for the channels relevant to the calling
        `webthing`.
        If all channels are 0, then switch the relay OFF.
        Notify all relevant changes to their `webthing`.
        """

        updated_things = set()
        # This is not a call to the self.set function, but the creation of a standard python set object (empty)

        logging.info(f'Dimmable_LED_strip_channels: reset {thing.channels} to {values}.')
        for channel_name in values.keys():
            self.PWM_board.channels[self.channels[channel_name]].duty_cycle = 0
            if self.value[channel_name] > 0:
                self.last_on_value[channel_name] = self.value[channel_name]
                self.value[channel_name] = 0
                for thing1 in self.things[channel_name]:
                    updated_things.add(thing1)

        for thing1 in updated_things:
            t1v = {k: v  for k, v in self.value.items() if k in thing1.channels}
            thing1.properties["channel_brightness"].value.notify_of_external_update(t1v)
            thing1.properties["colour"].value.notify_of_external_update(thing1.colour_convert(t1v))
            thing1.properties["brightness"].value.notify_of_external_update(scale(max(t1v.values()), 100, "brightness"))

        logging.info(f'Dimmable_LED_strip_channels: reset self.value = {self.value}.')
        if sum(self.value.values()) == 0:
            GPIO.output(self.on_off_channel, False)
            for thing2 in self.all_things:
                thing2.properties["on"].value.notify_of_external_update(False)
                thing2.properties["brightness"].value.notify_of_external_update(scale(0, 100, "brightness"))

    def channel_brightness(self, thing, values):
        """
        Set channel values (maybe to zero), but only for the channels relevant to the calling `webthing`.
        If all channels are 0, then switch the relay OFF.
        If any channel is non 0, then switch the relay ON.
        Notify all relevant changes to their `webthing`.
        """

        updated_things = set()
        # This is not a call to the self.set function, but the creation of a standard python set object (empty)

        logging.info(f'Dimmable_LED_strip_channels: channel_brightness {thing.channels} to {values}.')
        for channel_name, value in values.items():
            if self.value[channel_name] != value:
                for thing1 in self.things[channel_name]:
                    updated_things.add(thing1)
            self.value[channel_name] = value
            self.PWM_board.channels[self.channels[channel_name]].duty_cycle = self.__rectified_channel(value, channel_name)

        for thing1 in updated_things:
            t1v = {k: v  for k, v in self.value.items() if k in thing1.channels}
            thing1.properties["channel_brightness"].value.notify_of_external_update(t1v)
            thing1.properties["colour"].value.notify_of_external_update(thing1.colour_convert(t1v))
            thing1.properties["brightness"].value.notify_of_external_update(scale(max(t1v.values()), 100, "brightness"))

        logging.info(f'Dimmable_LED_strip_channels: channel_brightness self.value = {self.value}.')
        if sum(self.value.values()) == 0:
            GPIO.output(self.on_off_channel, False)
            for thing2 in self.all_things:
                thing2.properties["on"].value.notify_of_external_update(False)
        else:
            GPIO.output(self.on_off_channel, True)
            for thing2 in self.all_things:
                if max([v  for k, v in self.value.items() if k in thing2.channels]) > 0:
                    thing2.properties["on"].value.notify_of_external_update(True)

    def channel_curve(self, value):
        logging.info(f'Dimmable_LED_strip_channels: command to adjust channel curves to {value}.')
        for c in value.keys():
            self.channel_curves[c] = {float(k): v  for k, v in value[c].items()}

        for thing2 in self.all_things:
            thing2.properties["channel_curve"].value.notify_of_external_update(self.channel_curves)


class Dimmable_LED_strip_webthing(Thing):
    """
    This class is the logic layer presented to the web for consumption by webthing clients or a webthing gateway.
    It wraps and is separate from the Hardware LED strip channels control because webthings can share one or more
    channels.
    """

    # Take example on:
    # https://github.com/WebThingsIO/webthing-python/blob/5b779b5d3e545c93d636a0f6fac1582512cba62d/example/multiple-things.py#L161
    def __init__(self, uritype, urilocation, uriname, name, description, channels, LED_strip_channels):
        logging.info(f'{name}: initialising webthing.')

        Thing.__init__(
            self,
            f'{uritype}.{urilocation}.{uriname}',
            name,
            ['Light'],
            description
        )

        self.LED_strip_channels = LED_strip_channels
        self.channels           = channels

        rgb = len(set(channels) & {"Red", "Green", "Blue"}) > 0
        w   = len(set(channels) & {"White"}) > 0
        if rgb & w:
            self.colour_type = "RGBW"
        elif rgb:
            self.colour_type = "RGB"
        elif w:
            self.colour_type = "W"
        else:
            self.colour_type = "Other"

        LED_strip_channels.register_thing_with_LED_strip_channels(self)

        # Purpose:
        #   Provide location information for the list menu addon
        #   The list menu addon sorts webthings according to their location and
        #   groups webthings that provide access to the same device in
        #   different guises.
        self.add_property(
            Property(self,
                     'location',
                     Value(f'{uritype}:{urilocation}:{uriname}'),
                     metadata={
                         '@type':       'LocationProperty',
                         'title':       'Location',
                         'type':        'string',
                         'readOnly':    True,
                         'description': 'Where the webthing is located and '
                         'what it is: <type>:<location>:<name>, where '
                         '<location> = <property name>.<floor/zone>.<area/room>, '
                         'and <name> = <unified device>.<atomic device>',
                     }))

        # Purpose:
        #   1/ Switch lights on and off
        #   2/ Compatibility with default schema
        self.add_property(
            Property(self,
                     'on',
                     Value(False, self.OnOff),
                     metadata={
                         '@type':       'OnOffProperty',
                         'title':       'On/Off',
                         'type':        'boolean',
                         'description': 'Whether the lamp is turned on',
                     }))

        # Purpose:
        #   1/ Change the overall brightness of a LED strip, but keeping the same hue
        #   2/ Compatibility with default schema
        self.add_property(
            Property(self,
                     'brightness',
                     Value(0, self.brightness),
                     metadata={
                         '@type':       'BrightnessProperty',
                         'title':       'Brightness',
                         'type':        'number',
                         'description': 'The overall brightness level of the light from 0 to 100',
                         'unit':        'percent',
                     }))

        # Purpose:
        #   1/ Change the colour of the LED strip, similar to Channel Brightness but less precise
        #   2/ Compatibility with default schema
        #if len(set(channels) & {"Red", "Green", "Blue"}) > 0:
        self.add_property(
            Property(self,
                     'colour',
                     Value("#000000", self.colour),
                     metadata={
                         '@type':       'ColorProperty',
                         'title':       'Colour',
                         'type':        'string',
                         'description': 'The colour of the light #000000 to #ffffff',
                         'unit':        'hexadecimal value',
                     }))

        # Purpose:
        #   Change the brightness of LED channels independently and with fine grain (precision to about 1/1000).
        self.add_property(
            Property(self,
                     'channel_brightness',
                     Value({c: 0.0 for c in channels}, self.channel_brightness),
                     metadata={
                         '@type':       'ChannelBrightnessProperty',
                         'title':       'Channel brightness',
                         'type':        'object',
                         'description': 'Control the brightness of each channel separately, value from 0.0 to 1.0',
                         'unit':        '1 = fully on',
                     }))

        # Purpose:
        #   Edit the channel curve.
        self.add_property(
            Property(self,
                     'channel_curve',
                     Value(LED_strip_channels.channel_curves, self.channel_curve),
                     metadata={
                         '@type':       'ChannelCurveProperty',
                         'title':       'Channel curve',
                         'type':        'object',
                         'description': 'Control the channel curves (data calibration of PWM+MOSFET)',
                         'unit':        '{channel: {brightness: PWM ratio}}',
                     }))

        logging.info(f'{name}: initialised webthing.')

    def colour_convert(self, value):
        """
        ...
        """

        r = value["Red"]   if "Red"   in value else 0
        g = value["Green"] if "Green" in value else 0
        b = value["Blue"]  if "Blue"  in value else 0
        w = value["White"] if "White" in value else 0

        c = "#000000"

        if   self.colour_type == "RGB":
            c = f"#{scale(r, 255, 'Hex colour'):02x}{scale(g, 255, 'Hex colour'):02x}{scale(b, 255, 'Hex colour'):02x}"
        elif self.colour_type == "W":
            c = "#" + f"{scale(r, 255, 'Hex colour'):02x}" * 3
        elif self.colour_type == "RGBW":
            W = w - min((r, g, b))
            if w > 0:
                M = W / w - max((r, g, b))
                r += M
                g += M
                b += M
            c = f"#{scale(r, 255, 'Hex colour'):02x}{scale(g, 255, 'Hex colour'):02x}{scale(b, 255, 'Hex colour'):02x}"

        logging.debug(f"{self.title}: convert colour {value} for {self.colour_type} -> {c}.")
        return c

    def OnOff(self, value):
        logging.info(f'{self.title}: command to switch lights {"ON" if value else "OFF"}.')
        self.LED_strip_channels.OnOff(self, value)

    def brightness(self, value):
        logging.info(f'{self.title}: command to alter light brightness to {value}.')
        self.LED_strip_channels.brightness(self, value)

    def colour(self, value):
        logging.info(f'{self.title}: command to alter light colour to {value}.')
        self.LED_strip_channels.colour(self, value)

    def channel_brightness(self, value):
        logging.info(f'{self.title}: command to adjust light channels to {value}.')
        filtered_value = {k: v  for k, v in value.items() if k in self.channels}
        if len(filtered_value) > 0:
            self.LED_strip_channels.channel_brightness(self, filtered_value)

    def channel_curve(self, value):
        logging.info(f'{self.title}: command to adjust channel curves to {value}.')
        self.LED_strip_channels.channel_curve(value)


"""
    Dimmable_LED_strip_webthing.add_available_action(
        'fade',
        {
            'title': 'Fade',
            'description': 'Fade the lamp to a given level',
            'input': {
                'type': 'object',
                'required': [
                    'brightness',
                    'duration',
                ],
                'properties': {
                    'brightness': {
                        'type': 'integer',
                        'minimum': 0,
                        'maximum': 100,
                        'unit': 'percent',
                    },
                    'duration': {
                        'type': 'integer',
                        'minimum': 1,
                        'unit': 'milliseconds',
                    },
                },
            },
        },
        FadeAction)

    Dimmable_LED_strip_webthing.add_available_event(
        'overheated',
        {
            'description':
            'The lamp has exceeded its safe operating temperature',
            'type': 'number',
            'unit': 'degree celsius',
        })

    return Dimmable_LED_strip_webthing

"""


def load_calibration(channel):
    with open(f"Calibration-channel{channel}.pkl", "rb") as f:
        return pickle.load(f)


class Weather_measurement_webthing(Thing):
    """
    This class defines a webthing that communicates with the BME280 PCB over
    I2C to collect weather sensing measurements, i.e. temperature, humidity and
    pressure.
    """


    def __init__(self, uritype, urilocation, uriname, name, description, i2c_bus):
        logging.info(f'{name}: initialising webthing.')

        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c_bus, address=0x76)
        self.bme280.sea_level_pressure = 1013.25
        logging.info(f'STT {self.bme280.measurement_time_typical}ms')
        logging.info(f'STM {self.bme280.measurement_time_max}ms')

        Thing.__init__(
            self,
            f'{uritype}.{urilocation}.{uriname}',
            name,
            ['TemperatureSensor', 'HumiditySensor', 'BarometricPressureSensor'],
            description
        )

        self.readings = self.all_sensor_readings()
        self.readings_notified = {k: 0 for k in self.readings}
        self.readings_change_count = {k: 0 for k in self.readings}
        self.readings_change_tolerance = {k: 0.6 for k in self.readings}
        self.readings_change_tolerance["temperature"] = 0.06
        self.readings_digits = {k: 0 for k in self.readings}
        self.readings_digits["temperature"] = 1

        logging.info(f'Initial sensor readings: {self.readings}')
        logging.info(f'Initial change count: {self.readings_change_count}')
        logging.info(f'Change tolerance: {self.readings_change_tolerance}')

        self.add_property(
            Property(
                self,
                'temperature',
                Value(self.readings["temperature"]),
                metadata={
                     '@type':       'TemperatureProperty',
                     'title':       'Temperature',
                     'type':        'number',
                     'readOnly':    True,
                     'description': 'Temperature measured in °C',
                     'multipleOf':  0.1,
                     'unit':        '°C',
                }
            )
        )

        self.add_property(
            Property(
                self,
                'relative_humidity',
                Value(self.readings["relative_humidity"]),
                metadata={
                     '@type':       'HumidityProperty',
                     'title':       'Relative Humidity',
                     'type':        'integer',
                     'readOnly':    True,
                     'description': 'Relative humidity in %',
                     'unit':        '%RH',
                     'minimum':     0,
                     'maximum':     100,
                }
            )
        )

        self.add_property(
            Property(
                self,
                'pressure',
                Value(self.readings["pressure"]),
                metadata={
                     '@type':       'BarometricPressureProperty',
                     'title':       'Pressure',
                     'type':        'integer',
                     'readOnly':    True,
                     'description': 'Air pressure in hecto-Pascals',
                     'unit':        'hPa',
                }
            )
        )

        self.add_property(
            Property(
                self,
                'all_sensor_readings',
                Value(self.readings),
                metadata={
                     '@type':       'AllSensorReadingsProperty',
                     'title':       'Temperature, Humidity & Pressure',
                     'type':        'object',
                     'readOnly':    True,
                     'description': 'Air temperature, relative humidity and pressure',
                     'unit':        '{°C, %RH, hPa}',
                }
            )
        )

#        self.properties["all_sensor_readings"].value.notify_of_external_update(self.readings)
#        for k in self.readings:
#            self.properties[k].value.notify_of_external_update(self.readings[k])

        asyncio.ensure_future(self.property_update_loop())
        asyncio.ensure_future(self.door_watch_event_loop())


    def all_sensor_readings(self):
        return {
            "temperature":          self.bme280.temperature,
            "relative_humidity":    self.bme280.relative_humidity,
            "pressure":             self.bme280.pressure,
            #"altitude":             self.bme280.altitude,
        }


    async def property_update_loop(self):
        try:
            while True:
                self.readings = self.all_sensor_readings()
                notified = False

                for k in self.readings:
                    if ((math.fabs(self.readings_notified[k] - self.readings[k])
                         < self.readings_change_tolerance[k])
                        or
                        (round(self.readings[k], self.readings_digits[k])
                         == self.readings_notified[k]
                    )):
                        self.readings_change_count[k] = 0
                    else:
                        self.readings_change_count[k] += 1

                        if ((self.readings_change_count[k] > 4)
                            or
                            (math.fabs(self.readings_notified[k] - self.readings[k])
                             > 10 * self.readings_change_tolerance[k])
                        ):
                            self.readings_change_count[k] = 0
                            if self.readings_digits[k] <= 0:
                                self.readings_notified[k] = int(round(self.readings[k], self.readings_digits[k]))
                            else:
                                self.readings_notified[k] = round(self.readings[k], self.readings_digits[k])

                            self.properties[k].value.notify_of_external_update(self.readings_notified[k])

                            logging.info(f'Sensor update: {k} = {self.readings[k]:0.2f}')
                            notified = True

                if notified:
                    self.properties["all_sensor_readings"].value.notify_of_external_update(self.readings_notified)

                # sleep until the next whole 10 seconds
                await asyncio.sleep(10.01 - time.time() % 10)
        except KeyboardInterrupt:
            pass


    async def door_watch_event_loop(self):
    # TODO: experiment when sensor will be in the porch and see if door opening
    # or closing causes identifiable pressure changes.
    # play also with IIR settings - self.bme280.iir_filter = IIR_FILTER_X{2,4,8,16}
        try:
            p = [0] * 120
            n = 0
            pmin, pmax, psum, pssq = 0, 0, 0, 0
            await asyncio.sleep(60.01 - time.time() % 60)

            while True:
                p[n] = round(self.bme280.pressure, 2)
                if n == 0:
                    pmin, pmax, psum, pssq = p[n], p[n], p[n], p[n] ** 2
                else:
                    if p[n] < pmin:
                        pmin = p[n]
                    elif p[n] > pmax:
                        pmax = p[n]
                    psum += p[n]
                    pssq += p[n] ** 2

                n = (n + 1)
                if n == 120:
                    n = 0
                    pavg = psum / 120
                    pstddev = math.sqrt(pssq / 120 - pavg ** 2)
                    print(f"{time.strftime('%H:%M', time.localtime(time.time() - 55))}", end=" ")
                    print(f"{''.join([' -=≡#'[x] if x < 5 else '█' for x in (int(math.floor(math.fabs((v - pavg) * 50))) for v in p)])}", end="  ")
                    #print(f"{''.join([' -=≡#'[x] if x < 5 else '█' for x in (int(math.floor(math.fabs((v - pavg) / pstddev))) for v in p)])}", end="  ")
                    print(f"{pmin:0.2f} {pmax:0.2f} {pavg:0.2f} {pstddev:0.3f}")
                    #print([pmin, pmax, round(pavg, 3), round(pstddev, 5)])
                    #print(f"{[int(round((v - pavg) / pstddev, 0)) for v in p]}".translate({ord(c): None for c in "',"}))
                    #print(f"{['-' if math.fabs(v - pavg) < pstddev else v for v in p]}".translate({ord(c): None for c in "',"}))

                # sleep until the next whole half-second
                await asyncio.sleep(0.505 - time.time() % 0.5)
        except KeyboardInterrupt:
            pass


def run_server():
    logging.basicConfig(
        level  = logging.DEBUG,
        format = "%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )

    logging.info('run_server: configure GPIO')
    i2c_bus = busio.I2C(board.SCL, board.SDA)               # set-up the I2C communication bus
    GPIO.setmode(GPIO.BCM)
    # Notes:
    #   1/ Every MOS FET board behaves differently: change the curves to match your equipment.
    #   2/ Notice how I swapped channels, this was to make it easier to fine tune the relative
    #      importance of the various channels (so that when a colour is requested the LEDs show
    #      a good approximation of the intended colour.
    curves = []
    curves.append(load_calibration(0))
    curves.append(load_calibration(1))
    curves.append(load_calibration(2))
    curves.append(load_calibration(3))

    LED_strip_channels = Dimmable_LED_strip_channels(23, i2c_bus, 991, {"Red": 0, "Green": 1, "Blue": 3, "White": 2},
        # Approximately good curves for my set-up (hand & eye tuned):
        {"Red":   curves[0],
         "Green": curves[1],
         "Blue":  curves[3],
         "White": curves[2],
        #{"Red":   {0.0001:0.031 , 0.5:0.11, 0.93:0.23, 0.99:0.8},
        # "Green": {0.0001:0.0343, 0.5:0.09, 0.93:0.20, 0.99:0.4},
        # "Blue":  {0.0001:0.24  , 0.5:0.6 , 0.93:0.77, 0.99:0.95},
        # "White": {0.0001:0.0075, 0.83:0.05, 0.93:0.2, 0.99:0.3},
         }
    )

    urilocation = 'am56.GF.Porch'
    logging.info('run_server: define thing: Dimmable_RGB_LED_strip')
    Dimmable_RGB_LED_strip   = Dimmable_LED_strip_webthing('powerled.rgb', urilocation, 'Porch LED.Colour',
                                                           'Coloured light in the porch',
                                                           'Dimmable coloured LED strip in the porch',
                                                           ["Red", "Green", "Blue"],
                                                           LED_strip_channels,
                                                          )
    logging.info('run_server: define thing: Dimmable_White_LED_strip')
    Dimmable_White_LED_strip = Dimmable_LED_strip_webthing('powerled.w', urilocation, 'Porch LED.White',
                                                           'White light in the porch',
                                                           'Dimmable white LED strip in the porch',
                                                           ["White"],
                                                           LED_strip_channels,
                                                           )
    logging.info('run_server: define thing: Dimmable_RGBW_LED_strip')
    Dimmable_RGBW_LED_strip  = Dimmable_LED_strip_webthing('powerled.rgbw', urilocation, 'Porch LED.Colour & white',
                                                           'Coloured and white lights in the porch',
                                                           'Dimmable coloured and white LED strips in the porch',
                                                           ["Red", "Green", "Blue", "White"],
                                                           LED_strip_channels,
                                                           )

    Weather_measurements     = Weather_measurement_webthing('sensor.thp', urilocation, 'Porch sensors.°C, %RH, hPa',
                                                           'Weather measurements in the porch',
                                                           'Temperature, humidity and pressure measurements in the porch',
                                                           i2c_bus,
                                                           )

    logging.info('run_server: define things: Dimmable_LED_strip_webthings')
    Dimmable_LED_strip_webthings = [Dimmable_RGB_LED_strip, Dimmable_White_LED_strip, Dimmable_RGBW_LED_strip,]
    Sensor_webthings = [Weather_measurements,]
    logging.info('run_server: define server')
    Server = WebThingServer(MultipleThings(Dimmable_LED_strip_webthings + Sensor_webthings,
                                           'Porch lights & sensors'),
                            port=8888, hostname='rpi3.local',
                           )

    try:
        logging.info('run_server: start')
        Server.start()
    except KeyboardInterrupt:
        pass
    finally:
        Dimmable_RGBW_LED_strip.OnOff(False)
        logging.info('run_server: stop')
        Server.stop()
        logging.info('run_server: stopped')
        GPIO.cleanup()
        logging.info('run_server: GPIO cleanup complete')


if __name__ == '__main__':
    run_server()

"""
TESTING 2020-09-24

python3
>>> import webthing_led_strip_12v_non_addressable
>>> webthing_led_strip_12v_non_addressable.run_server()

# Check there are no errors, lights are off and relay is off
# https://github.com/WebThingsIO/curl-examples

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": true}' http://<ip or domain>:8888/1/properties/on
# Check relay is on - White lights may be on or off depending on their last on state

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/1/properties/on
# Check lights are off and relay is off

p=0; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": true}' http://<ip or domain>:8888/$p/properties/on; sleep 3; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/$p/properties/on
# RGB lights and relay come on for three seconds, then off (if last on state was greater than 0)

p=2; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": true}' http://<ip or domain>:8888/$p/properties/on; sleep 3; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/$p/properties/on
# All lights (RGBW) and relay come on for three seconds, then off (if last on state was greater than 0)

(p=0; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": true}' http://<ip or domain>:8888/$p/properties/on; sleep 3; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/$p/properties/on)&
sleep 1
p=1; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": true}' http://<ip or domain>:8888/$p/properties/on; sleep 3; curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/$p/properties/on
# RGB lights and relay come on
# 1 second later White lights come on
# 2 seconds later RGB lights come off but relay stays on
# 1 second later White lights and relay switch off

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.5}}' http://<ip or domain>:8888/0/properties/brightness
# Blue only and relay come on

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.1, "Red": 0.3}}' http://<ip or domain>:8888/0/properties/brightness
# Blue reduces, Red comes one -> Pink

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/1/properties/on
# Nothing happens

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/0/properties/on
# Lights and relay switch off

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.1, "Red": 0.3}}' http://<ip or domain>:8888/0/properties/brightness
# RGB lights shine Pink, relay comes on

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.0, "Red": 0.0}}' http://<ip or domain>:8888/0/properties/brightness
# Lights and relay switch off

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.1, "Red": 0.3}}' http://<ip or domain>:8888/0/properties/brightness
# RGB lights shine Pink, relay comes on

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Red": 0.1, "Green": 0.3}}' http://<ip or domain>:8888/0/properties/brightness
# Blue stays, Red reduces, Green comes on, relay stays on

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Red": 0}}' http://<ip or domain>:8888/0/properties/brightness
# Turn off one colour at a time

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0}}' http://<ip or domain>:8888/0/properties/brightness
# Turn off one colour at a time

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Green": 0}}' http://<ip or domain>:8888/0/properties/brightness
# Turn off one colour at a time and switch relay off

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.5}}' http://<ip or domain>:8888/1/properties/brightness
# Relay and lights stay off - trying to turn Blue channel on on the White only light control!

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.5, White: 0.01}}' http://<ip or domain>:8888/1/properties/brightness
# Turns the white on, leaves the blue off, relay on

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.05, "White": 0.3}}' http://<ip or domain>:8888/0/properties/brightness
# Turns the blue on, does not change white brightness, relay stays on

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.3, "White": 0.3}}' http://<ip or domain>:8888/2/properties/brightness
# Turns white and blue brighter

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/2/properties/on
# Turns off lights and relay

curl -i -X PUT -H 'Content-Type: application/json' -d '{"brightness": {"Blue": 0.3, "White": 0.3}}' http://<ip or domain>:8888/2/properties/brightness
# Turns on white, blue and relay

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/0/properties/on
# Turns blue off

curl -i -X PUT -H 'Content-Type: application/json' -d '{"on": false}' http://<ip or domain>:8888/1/properties/on
# Turns white and relay off

"""

# vi:set expandtab ts=4 sw=4 tw=79:

"""
Module:     PWM_and_MOSFET_calibration.py

Purpose:
    Use once tool to help calibrate the sensitivity curves to control LED
    strips with module "webthing_dimmable_LED_strip.py".

    Use this module measure the voltage output for a sample of PWMs. the output
    of thie module is saved in a cs file which can be used by
    "Compute-LED-calibration.py" to generate a calibration curve, with manual
    tweaking.
    So that results can be compared on an equal footing, it is best to use
    exactly the same physical set-up for reading values, as small variance in
    resistor values would introduce significant differences.
    Therefore we only measure one channel at a time.

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
    2020-09-24: creation of this (almost) discardable code
    2020-10-07: V1.0
                final version, pycodestyle (some warnings ignored)

===============================================================================
Future:
    Nothing.

    This tool is used to fine tune the calibration curves with new hardware. As
    this is a hobby project, it is presently perfect in its imperfection:
    sufficiently good to do the job rather efficiently. Of course it is not
    production grade, it does not need to be.

Copyright:
    Alain P.M. Culos 2020, all rights reserved.

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
    Set a PWM channel to a given duty cycle (power a LED strip channel with a
    dimmed value).
    Read the ADC (lots of samples to ensure reading accuracy to about 1 /
    1000th) to measure the MOSFET output.

Physical diagram:
                         +-----+
                   +---->| ADC |<--- 1 channel <---+
                   |     +-----+                   |
                   v                               |
    +----+      +-----+  +-----+       +---------+ |                +------------+
    | 5V |----->| rPi |->| PWM |-4 ch->| MOS FET |-+-> 4 channels ->| LED strips |
    +----+      +-----+  +-----+       +---------+                  +------------+
                   |                        ^
                   v      +---------------+ |
    +-------+  +-------+  |  Transformer  | |
    | Mains |->| Relay |->| Mains --> LED |-+
    +-------+  +-------+  | strip voltage |
                          +---------------+

Wiring:
    For detail about the LED set-up, please read "webthing_dimmable_LED_strip.py".
    Below is the detail of the calibration set-up (ADC).

    Pi - ADC: I2C bus
        Pi: +3.3V, Pin01    -> ADS1115: V,   Pin1
        Pi: SDA, Pin03      -> ADS1115: SDA, Pin4
        Pi: SCL, Pin05      -> ADS1115: SCL, Pin3
        Pi: GND, Pin09      -> ADS1115: G,   Pin2

    ADC - MOS FET
        ADS1115: G,   Pin2  -> Point 1
        Point 1             -> MOS FET: Output V- of any channel
                               (right of a pair, open side of blocks)
        ADS1115: A0,  Pin7  -> Point 2
        Point 3             -> MOS FET: Output V+ of channel to be calibrated
                               (left of a pair, open side of blocks)

        +---------+                        +---------+                       +---------+
        | Point 1 |--- 6.8kOhm resistor ---| Point 2 |--- 20kOhm resistor ---| Point 3 |
        +---------+                        +---------+                       +---------+

        This is to bring the +12V down to below +3.3V that the ADC requires.
        Using a capacitor somewhere may help smooth (filter) the PWM and
        therefore allow us to speed up the calibration process, but as this is
        a once-off, I'll stay put with this set-up.
        We need a low-pass to cut-off all frequencies above 40Hz. But then the
        sample rate cannot exceed 40Hz either.
"""

import time
import board
import busio
import adafruit_pca9685                     # extension board that can produce
                                            # up to 16 HW PWMs 40 Hz to 1600 Hz.
import adafruit_ads1x15.ads1115             # ADC: analog to digital converter
import adafruit_ads1x15.analog_in

import numpy as np
import pandas as pd


i2c_bus = busio.I2C(board.SCL, board.SDA)   # set-up the I2C communication bus
pca = adafruit_pca9685.PCA9685(i2c_bus)     # set-up communication with the PWM
                                            # board
ads = adafruit_ads1x15.ads1115.ADS1115(i2c_bus, data_rate = 860, mode = 0)
                                            # set-up the ADC in fast continuous
                                            # mode sampling
ch0 = adafruit_ads1x15.analog_in.AnalogIn(ads, adafruit_ads1x15.ads1115.P0)
                                            # Use channel 0 of the ADC


def tp(frequency, channel, level, number_of_samples):
    return Test_PWM_power_output_with_LED_load(
               frequency, channel, level, number_of_samples)


def tpv(frequency, channel, level, number_of_samples):
    return Test_PWM_power_output_with_LED_load(
               frequency, channel, level, number_of_samples, "\r")


def Test_PWM_power_output_with_LED_load(
        frequency, channel, level, number_of_samples, endofline = "\n"):

    pca.frequency = frequency
    # Switch LED channel on, level = [0..0xfffe]
    pca.channels[channel].duty_cycle = level
    sum_m  = 0
    sum_m2 = 0

    sampling_start_time = time.time()
    # Wait 40ms before starting sampling, let the PWM+LED settle after power-on
    time.sleep(0.04)

    for _ in range(number_of_samples):
        measurement = ch0.voltage
        sum_m  = sum_m  + measurement
        sum_m2 = sum_m2 + measurement**2

    sampling_duration = time.time() - sampling_start_time
    # Switch LED channel off
    pca.channels[channel].duty_cycle = 0
    average = sum_m / number_of_samples

    print(f"{frequency:4d}Hz  PWM#{channel:02d}  Level=0x{level:04x}={level:05d}" +
          f"  ->  {average:5.3f}V" +
          f"  {number_of_samples} samples" +
          f"  in {sampling_duration*1000:1.0f}ms",
          end=endofline)

    # Allow LEDs to cool down for 40% of the time they were on
    time.sleep(sampling_duration * 0.4)

    return (average, sampling_duration)


def Variance(function, parameters, number_of_function_calls):
    """
    Variance runs the same measurement batches a number of times and calculates
    the standard deviation between the average measurements of those batches.
    When the standard deviation is low, we know we have an accurate, reliable
    measurement.
    I used Variance to observe how different parameters affected this accuracy,
    allowing me to chose the right frequency and the right sampling parameters.
    Only after this did I run a proper sampling batch of each channel.
    I tried a variety of different "Test_PWM_power_output_with_LED_load"
    functions with varying delays in various places, an initial delay of 40ms
    before sampling seems to work best, no delay necessary during sampling.
    I also tried changing the sampling rate, fast continuous mode works best.
    Finally I tried to use statistics at the sampling stage, but the stddev is
    way too large to be any use. It is best to sample a batch and see if those
    batches are stable with repetition.
    """
    sq = 0.0
    tm = 0.0
    tt = 0
    for loop in range(number_of_function_calls):
        print(f"Loop {loop+1:2d}/{number_of_function_calls}:   ", end="")
        (measurement, sampling_duration) = function(*parameters)
        tt = tt + sampling_duration
        tm = tm + measurement
        sq = sq + measurement**2

    average = tm / number_of_function_calls
    stddev = (sq / number_of_function_calls - average**2)**.5
    function_name = f"{function}".split(" ")[1]

    if function_name == "tp":
        frequency, channel, level, number_of_samples = parameters
        print(f"{function_name}, {number_of_function_calls} loops:" +
              f"  {frequency:4d}Hz  PWM#{channel:02d}  Level=0x{level:04x}={level:05d}" +
              f"  ->  average {average:5.3f}V,  {number_of_samples} measurements," +
              f"  stddev = {stddev:0.6f}V in {tt/number_of_function_calls*1000:1.0f}ms each")

def calibrate():
    try:
        test_channel, test_load = [
            (0, "RGB LED strip, 3 channels, Red wire"),
            (1, "RGB LED strip, 3 channels, Green wire"),
            (2, "White LED strip, 1 channel"),
            (3, "RGB LED strip, 3 channels, Blue wire"),
        ][3]

        """
        Variance(tp,   (1000, 2, 0x0fff,  1000), 20)
        Variance(tp,   (1000, 2, 0x0fff, 20000), 20)

        # First search & analysis
        values = list(np.arange(0, 1, 0.1)) + list(np.arange(1, 10, 1)) + list(np.arange(10, 105, 5))
        # Note: np.arange sometimes shows very small digits after many zeros, this does not happen
        # if we use integers and divide by 100 (.0, to make the numbers floats).

        # Second search & analysis
        values = list(map(lambda x: x/100.0, sorted(
                                                    set(range(  20,   100,   1)) |
                                                    set(range(  10,   150,   2)) |
                                                    set(range(   0,   300,   5)) |
                                                    set(range(   0,   400,  10)) |
                                                    set(range(   0,   600,  25)) |
                                                    set(range(   0,   800,  50)) |
                                                    set(range(6500,  8000,  50)) |
                                                    set(range(   0, 10001, 250))
                 )))
        """
        # Third search & analysis & Final calibration
        values = list(map(lambda x: x/100.0, sorted(
                                                    set(range(   0,    50,  25)) |
                                                    set(range(  50,   300,   3)) |
                                                    set(range( 300,   600,   5)) |
                                                    set(range( 600,  1200,  10)) |
                                                    set(range(1200,  2400,  20)) |
                                                    set(range(2400,  4800,  50)) |
                                                    set(range(4800, 10001, 100))
                 )))
        levels = list(map(lambda x: int(x / 100 * 0xfffe), values))

        # First search & analysis
        #frequency_first =  100
        #frequency_last  = 1600
        #number_of_steps =   15
        #frequency_step  = int((frequency_last - frequency_first) / number_of_steps)

        # Second search & analysis
        #frequency_first =  500
        #frequency_last  = 1000
        #frequency_step  =   50
        #frequencies     = list(range(frequency_first,
        #                             frequency_last + frequency_step,
        #                             frequency_step
        #                      ))

        # Third search & analysis
        #frequencies     = [991, 997, 1009]

        # Final calibration
        frequencies     = [991,]

        measurements = pd.DataFrame(columns=[
                           'Load name', 'Channel', 'Value (%)',
                           'Level', 'Frequency (Hz)', 'Voltage (V)'
                       ])

        #for k, value in enumerate(values):
        #    print(f"Value {value:6.2f}% = level 0x{levels[k]:04x} = {levels[k]:5d}")
        print(f"Number of levels: {len(values)}")
        print("")

        n_samples           = 25_000
        delta_from_max      =      0.0015 # V
        delta_from_previous =      0.0015 # V

        for frequency in frequencies :
            vl = list(zip(values, levels))

            value, level = vl[-1]
            measure, _ = tp(frequency, test_channel, level, n_samples)
            measurements.loc[len(measurements)] =   \
                (test_load, test_channel, value, level, frequency, measure)
            max_measure = measure
            n_max       = 0
            n_repeat    = 0
            pmeasure    = measure

            for value, level in vl[:-1]:
                #Variance(tpv, (frequency, test_channel, level, n_samples), 20)
                measure, _ = tp(frequency, test_channel, level, n_samples)
                measurements.loc[len(measurements)] =   \
                    (test_load, test_channel, value, level, frequency, measure)

                if measure >= (max_measure - delta_from_max):
                    n_max += 1
                    if n_max >= 3:
                        break
                else:
                    n_max = 0

                if measure > 2:
                    if abs(measure - pmeasure) <= delta_from_previous:
                        n_repeat += 1
                        if n_repeat >= 12:
                            break
                    else:
                        n_repeat    = 0
                        pmeasure    = measure

        print(measurements)
        print("Saving to csv... ", end="")
        measurements.to_csv(f"LED measurements - Channel {test_channel} - "
                            f"{test_load} - " +
                            f"{time.strftime('%Y-%m-%d %X',
                               time.localtime(time.time()))}.csv"
                           )
        print("Saved")

    except KeyboardInterrupt:
        pass
    finally:
        pca.channels[0].duty_cycle = 0
        pca.channels[1].duty_cycle = 0
        pca.channels[2].duty_cycle = 0
        pca.channels[3].duty_cycle = 0

calibrate()

# vi:set expandtab ts=4 sw=4 tw=79 ai si:

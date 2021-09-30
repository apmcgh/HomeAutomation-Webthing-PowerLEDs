"""
Module:     Compute-LED-calibration.py

Purpose:
    Use measurement results "LED measurements*.csv" to produce a "curve" that
    maps the intended brightness to the PWM duty cycle (LED intensity control
    value) in order to attempt to have as linear as possible a relationship
    between the "brightness" or "colour" values and the actual light emitted by
    the LEDs.
    Part of this is achieved by "calibrating", i.e. finding out the voltage
    output for a wide range of PWM values. This is the scientific part. The
    other part, the less sophiticated part, the subjective one, uses two
    parameters for each channel to attempt a best fit:
    1/ "zero" is the minimum PWM duty cycle required to light the channel at
    its lowest level.
    2/ "power" is a non linear bending of the curve, the higher the power thhe
    lower the curve goes in the middle, while keeping 0 and 1 as they are, this
    allows us to change the relative importance of the vraious channels so that
    they light up mostly proportionately to each other at various intensity
    levels.

Tests and adjustments:
    Every time a zero or a power is changed, this program must be run to
    produce the calibration curves and the webthing server must be restarted.
    It is possible to change the "curves" live via the "channel_curve" property,
    but I have not provided a user friendly means to do so.
    It's easier to just restart the webthing server.

    1/ Start the webthing server (webthing_dimmable_LED_strip.py), start the
    gateway, connect to it (browse to the gateway).
    Set the colour to pure white, then set the brightness to the minimum
    possible.
    All LED channels should be just lit a tiny bit, if not, adjust the zero
    values. If a zero value just a fraction smaller fails to light up its
    channel, then you have the right zero.

    2/ Set the colour to maximum saturation and value, then try various hues
    around the wheel.  Of particular interest are cyan, magenta and yellow. For
    instance if green dominates when the setting it for yellow, then the power
    for green must be increased or red decreased.

    3/ another way to test colour dominance is to set a colour to maximum
    value, then change the brightness (to 80%, 50%, 20%...) and see if the
    colour hue changes or only the intensity changes. If the hue changes so one
    channel comes to dominate, its power must be increased, or if a channel
    becomes too weak, then its power must be decreased.

Notes:
    1/ zeros are small values usually close to 0, most likely less than 0.1,
    they are most likely affected by the tolerance errors on the resistors of
    the MOSFET board (not tested)

    2/ powers should most likely be between 1 and 3, most probably close-ish to
    2. They are probably affected by the PWM resistor variance and by physics -
    the different LED wavelengths most likely respond differently to PWM and
    voltage, and their perceived brightness may not be solely correlated to the
    input voltage and waveform.

    3/ the values of zeros and powers in this file are only relevant for the
    hardware I used them on, they must be tailored to each and every distinct
    hardware set-up.

    4/ same goes with the measurements, these must be taken for each channel of
    each hardware set-up. See "PWM_and_MOSFET_calibration.py"
    I have taken the measurements with the LEDs connected (in technical jargon,
    with the "load" on). I did not try without the load so I cannot say which
    gives the best results.

===============================================================================
Author:     Alain Culos
            programming-electronics@asoundmove.net

History:
    2020-10-04: Full functionality: create calibration curves from a
                combination of channel voltage measurement and a few intuitive
                parameters (zeros, powers).
    2020-10-05: V1.0
                Explanatory comments
    2020-10-09: V1.1
                Formatting to text width = 79 characters, pycodestyle
                Ignored some of the warnings - for higher legibility.

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
    includes the development process even if this software is not used in the
    final commercial product.
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
    power. The author is not an electrician or an electronics specialist so I
    cannot provide advice. You should also undesrtand the relationships between
    software and hardware as overheating electronics can cause fires and bare
    wires can cause electrocution.

    The purpose of sharing the present file is for self learning and exchange
    with like-minded people.

===============================================================================
"""

import pandas
import numpy
import pickle


def compute_calibration(filename, channel, zeros, powers):

    # Load the measurements (essentially value vs voltage for a given frequency
    # of a given channel)
    caldata = pandas.read_csv(filename)

    # Extract only the data relevant for calibration purposes.
    # Either adjust the frequency to the one relevant to your set-up or remove
    # the filter but make sure the measurements only record a single frequency.
    d = caldata[caldata['Frequency (Hz)'] == 991].loc[:, [
        'Value (%)', 'Voltage (V)']].values

    # sort the data by order of values (first column)
    d.sort(axis=0)

    # find the smallest and largest voltages measured (2nd column)
    min_vo = numpy.min(d[:, 1])
    max_vo = numpy.max(d[:, 1])

    # use the relevant zero and power
    zero  = zeros[channel]
    power = powers[channel]
    vo_scale = 1 / (max_vo - min_vo)

    # ix = index, va = value (PWM duty cycle), vo = measured voltage under load
    # s?? = start
    # p?? = previous
    ix,  va,  vo  = (1, d[1, 0], d[1, 1])
    six, sva, svo = (ix, va, vo)

    # Curve = {Ratio of intended brightness (take Voltage as a first measure):
    # ratio fo PWM duty cycle, ...}
    # initialise the curve with 0 and the first point
    curve = {0: 0, }
    curve[(vo - min_vo) * vo_scale] = zero + (1 - zero) * (va / 100)**power

    # set the tolerance, this can be changed to something larger if you want
    # less segments, it will produce a less acurate mapping, but it may be good
    # enough (I did not test other values).
    tolerance = (max_vo - min_vo) / 1024
    lend = len(d)

    # Iterate until we scanned the whole set of measurements
    # This loop creates all the segments of the calibration curve
    while (ix < lend-1):
        error = 0

        # Iterate until the tolerance is exceeded, the previous point will
        # provide the best fast fit (naïve search)
        while (error <= tolerance) and (ix < lend-1):
            pix, pva, pvo = (ix, va, vo)
            ix += 1
            va,  vo = (d[ix, 0], d[ix, 1])
            # [.0] = Value (% of duty cycle)
            # [.1] = Voltage

            # We draw a line from the first point (six) to the last (ix) and
            # calculate the vertical distance between that line and each
            # measurement. If we are within the tolerance we keep looking for a
            # longer segment, otherwise we stop and revert one position (last
            # error wihtin tolerance)
            error = numpy.max(numpy.abs(
                d[six:(ix+1), 1] - svo -
                (vo - svo) * (d[six:(ix+1), 0] - sva) / (va - sva)
            ))

        if (error > tolerance):
            ix,  va,  vo = (pix, pva, pvo)

        # Record the last segment found
        curve[(vo - min_vo) * vo_scale] = zero + (1 - zero) * (va / 100)**power

        # prepare to find the net segment
        six, sva, svo = (ix, va, vo)

    # remove the first and last elements of the curve as they are implied when
    # using the calibration data in "webthing_dimmable_LED_strip.py"
    curve.pop(0)
    curve.pop(1.0)

    # save the curve object for easy retrieval and so we do not have to compute
    # this every time we start the webthing server.
    with open(f"Calibration-channel{channel}.pkl", "wb") as f:
        pickle.dump(curve, f, pickle.HIGHEST_PROTOCOL)

    print(f"Saved file 'Calibration-channel{channel}.pkl': {curve}.")


# Below, use data specific to your hardware set-up:
#   See comments at the begining of this file for how to set zeros and power
#   and how to take the measurements.
#   Change file names to match your set-up.

# Red Green White Blue
zeros = [0.031, 0.0338, 0.0073, 0.23]
powers = [1.59, 1.63, 1.29, 2.2]

compute_calibration(
    'LED measurements - Channel 2 - White LED strip, 1 channel '
                        '- 2020-10-03 10:57:23.csv',            2,
    zeros, powers
)
compute_calibration(
    'LED measurements - Channel 0 - RGB LED strip, 3 channels, '
                        'Red wire - 2020-10-03 16:45:22.csv',   0,
    zeros, powers
)
compute_calibration(
    'LED measurements - Channel 1 - RGB LED strip, 3 channels, '
                        'Green wire - 2020-10-03 20:10:48.csv', 1,
    zeros, powers
)
compute_calibration(
    'LED measurements - Channel 3 - RGB LED strip, 3 channels, '
                        'Blue wire - 2020-10-04 00:43:18.csv',  3,
    zeros, powers
)

# vi:set expandtab ts=4 sw=4 tw=79:

# HomeAutomation-Webthing-PowerLEDs

A Home Automation project based on the Webthings framework to control power LED
strips.


## Definitions


**Home Automation:**  
The craft, or technical art, of making things happen in the house, not
previously deemed possible.  
For example: switching a light from a new place without re-wiring the house.


**Webthings:**  
(https://webthings.io/) An open platform for monitoring and controlling devices
over the web.  
In other words: it is a set of software tools and libraries that help put
together existing software as well as your own, to provide a means to build home
automation solutions.  
The platform comprises of two parts:  
 + The Gateway
 + The Framework

The Gateway is a web app that provides the on screen controls (e.g. light
switches) to your home devices, via a webpage.  

The Framework allows you to make your own devices controlable by the gateway.


**Webthing:**  
One such piece of software, possibly developed by yourself, to control your home
device.  
The present project is a webthing.


**Power LEDs:**  
LED strips of which the light intensity (how bright or dim they shine) is
controlled by controlling the power that feeds them.  
These LEDs are **not** addressable, they are all lit to the same brightness.


## Project


### Hardware:


Design and build an electronic controller based around the raspberry Pi zero to
finely control the power that feeds LED strips by means of a PWM. I designed the
device to drive 4 channels: red, green, blue and white.

The PWM output of the Pi cannot drive power into the LED strips, it would burn
the Pi, so instead the PWM drives high frequency "relays" (MOS FETs).

The key challenge here was the complex relationship between PWM ratios,
frequency and actual output power, different on each channel and different
depending on the load (red, green, blue and white all behave differently).

For wiring details, please see documentation inside the main program file:

`code/webthing_dimmable_LED_strip.py`


### Software:


The learning curve to fit within the Webthing framework is relatively steep, but
worth it. Please note that this is work in progress (toppled over by other
priorities).

The purpose of the software is to provide a means to reasonably acurately
control the colour and brightness of the LED strips (one RGB, one White).

The main program file, which runs on python3, is essentially a micro server that
gets called by the Webthing Gateway (the interface that provides the physical
controls). How this program fits in with the Gateway is outside the scope of
this project at this point in time.

`code/webthing_dimmable_LED_strip.py`

In addition to the file above, I wrote two other one-time use programs (I do not
intend to built multiple similar units) to first take the measurement of the
power driven by each PWM, then assit me in adjusting parameters to calibrate the
PWM to brightness for each channel relatively to each other.

`code/PWM_and_MOSFET_calibration.py`  
and  
`code/Compute-LED-calibration.py`


### Future:


It is my intention to convert this project to a tutorial, although life throws
curved balls that mean this is not a priority any longer. Hopefully the
documentation in the code in its present state is sufficiently explanatory. So
please enjoy and peruse (if you do this for fun only). If you do earn money in
this field and this project contributes in any way to a commercial endeavour,
please do feel obliged to share a portion of your earnings towards helping make
this project better. Generous contributions would change my priorities.

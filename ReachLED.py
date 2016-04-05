#!/usr/bin/python

# ReachView code is placed under the GPL license.
# Written by Egor Fedorov (egor.fedorov@emlid.com)
# Copyright (c) 2015, Emlid Limited
# All rights reserved.

# If you are interested in using ReachView code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of ReachView.

# ReachView is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ReachView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ReachView.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
from multiprocessing import Process
from GPIO import GPIO

class ReachLED:

    pwm_prefix = "/sys/class/pwm/pwmchip0/"

    def __init__(self):
        self.pins = [GPIO(12), GPIO(13), GPIO(182)] # green, red, blue

        # thread, used to blink later
        self.blinker_thread = None

        # to stop blinker later
        self.blinker_not_interrupted = True

        # keep current state in order to restore later
        self.current_blink_pattern = ""

        self.colors_dict = {
            "off": [0, 0, 0],
            "red": [1, 0, 0],
            "green": [0, 1, 0],
            "blue": [0, 0, 1],
            "white": [1, 1, 1],
            "yellow": [1, 1, 0],
            "cyan": [0, 1, 1],
            "magenta": [1, 0, 1],
            "orange": [1, 0.4, 0],
            "weakred": [0.1, 0, 0]
        }

        # channel numbers
        self.pwm_channels = [0, 1, 2] # red, green, blue

        # first, we need to change the pin's pinmux to mode1
        for pin in self.pins:
            pin.setPinmux("mode1")

        # then, export the 3 pwn channels if needed
        for ch in self.pwm_channels:
            if not os.path.exists(self.pwm_prefix + "/pwm" + str(ch)):
                with open(self.pwm_prefix + "export", "w") as f:
                    f.write(str(ch))

        # enable all of the channels
        for ch in self.pwm_channels:
            with open(self.pwm_prefix + "pwm" + str(ch) + "/enable", "w") as f:
                f.write("1")

        # set period
        for ch in self.pwm_channels:
            with open(self.pwm_prefix + "pwm" + str(ch) + "/period", "w") as f:
                f.write("1000000")

        # turn off all of it by default
        #for ch in self.pwm_channels:
        #    self.setDutyCycle(ch, 0)

    def set_duty_cycle(self, channel, percentage = None):
        # 0% = 1000000
        # 100% = 0

        duty_value = (100 - percentage) * 10000
        duty_value = int(duty_value)
        
        with open(self.pwm_prefix + "pwm" + str(channel) + "/duty_cycle", "w") as f:
            f.write(str(duty_value))

    def pulse_color(self, color, delay = None, power_percentage = None):

        if delay == None:
                delay = 0.5

        if power_percentage == None:
            power_percentage = 100

        number_of_steps = 10
        step = power_percentage / number_of_steps
        delay = delay * 0.5 / number_of_steps

        if color in self.colors_dict:
            for brightness in xrange(0, power_percentage + step, step):
                for i in range(0, 3):
                    self.set_duty_cycle(i, self.colors_dict[color][i] * brightness)
                time.sleep(delay)
            for brightness in xrange(power_percentage, 0 - step, -step):
                for i in range(0, 3):
                    self.set_duty_cycle(i, self.colors_dict[color][i] * brightness)
                time.sleep(delay)
            return 0
        else:
            return -1

    def set_color(self, color, power_percentage=None):

        # defalt power percentage value
        if power_percentage == None:
            power_percentage = 100

        if color in self.colors_dict:
            for i in range(0, 3):
                self.set_duty_cycle(i, self.colors_dict[color][i] * power_percentage)

            return 0
        else:
            # no such color available :(
            return -1

    def start_blinker(self, pattern, delay=None, pulse=None):
        # start a new thread that blinks

        self.current_blink_pattern = pattern

        if self.blinker_thread == None:
            self.blinker_not_interrupted = True
            self.blinker_thread = Process(target = self.blink_pattern, args = (pattern, delay, pulse))
            self.blinker_thread.start()
        else:
            # we already have a blinker started and need to restart it using new colors
            self.stop_blinker()
            self.start_blinker(pattern, delay, pulse)

    def stop_blinker(self):
        # stop existing thread

        self.blinker_not_interrupted = False

        if self.blinker_thread is not None:
            self.blinker_thread.join()
            self.blinker_thread = None

    def blink_pattern(self, pattern, delay=None, pulse=None):
        # start blinking in a special pattern
        # pattern is a string of colors, separated by commas
        # for example: "red,blue,off"
        # they will be flashed one by one
        # and separated by a time of delay, which 0.5s by default
    
        if pulse == None:
            pulse = False

        color_list = pattern.split(",")

        if delay == None:
            delay = 0.5

        while self.blinker_not_interrupted:
            for color in color_list:
                if pulse:
                    self.pulse_color(color, delay)
                else:
                    self.set_color(color)
                    time.sleep(delay)

def test():
    led = ReachLED()
    print("Starting...")
    led.set_duty_cycle(0, 0)
    led.set_duty_cycle(0, 0)
    led.set_duty_cycle(0, 0)

    time.sleep(1)
    print("After pause...")
    print("Channel 0")
    led.set_duty_cycle(0, 100)
    time.sleep(1)
    print("Channel 1")
    led.set_duty_cycle(0, 0)
    led.set_duty_cycle(1, 100)
    time.sleep(1)
    print("Channel 2")
    led.set_duty_cycle(1, 0)
    led.set_duty_cycle(2, 100)
    time.sleep(1)

if __name__ == "__main__":
    # test()
    led = ReachLED()

    if len(sys.argv) < 2:
        print("You need to specify a color")
        print("List of colors:")

        colors = ""
        for color in led.colors_dict:
            colors += color + ", "

        print(colors)

    else:
        delay = 1
        if led.pulse_color(sys.argv[1], delay, 100) < 0:
            print("Can't set this color. You may add this in the colors_dict variable")
        else:
            while True:
                time.sleep(delay)
                led.pulse_color(sys.argv[1], delay, 100)







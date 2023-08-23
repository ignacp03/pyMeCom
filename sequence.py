"""
Sequence tests for PID parameters optimization
"""
import logging
from mecom import MeCom, ResponseException, WrongChecksum
from serial import SerialException
from control_test import BlueLDD, pulse_shape
import time
import numpy as np

start = time.time()
COM_port = 'COM6'
laser = BlueLDD(port=COM_port)
#Settings
settings_update = True
ramp_time = 0.002 #s
high_time = 0.005 #s
high_power = 1 #W
sampling_time = 10 #u.s
if settings_update:
    pulse = pulse_shape(ramp_time,high_time, high_power, sampling_time)
else:
    pulse = np.loadtxt('blue_pulse.csv', delimiter = ';')

#PID param
pid_update = True
Kp = 0.5 #A/W
Ki = 0.1 #s
Kd = 1e-09
slope_lim = 0.1 #W/us
if pid_update:
    laser.set_PID_LPC_params(Kp, Ki, Kd, slope_lim)






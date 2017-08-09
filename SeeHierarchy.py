#!/usr/bin/python
from __future__ import print_function, absolute_import, division

import numpy as np
import pylibapogee.pylibapogee as apg
import pylibapogee.pylibapogee_setup as SetupDevice

print("Trying to find and connect with camera")
#look for usb cameras first
devices = SetupDevice.GetUsbDevices()
print("Number of devices:", len(devices))
print("Device:", devices)
print()

# Connecting to camera
cam = SetupDevice.CreateAndConnectCam(devices[0])
print(help(cam))

cam.CloseConnection()

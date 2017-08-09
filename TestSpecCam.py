#!/usr/bin/python
from __future__ import print_function, absolute_import, division

import sys

from astropy.io import fits
import numpy
import pylibapogee.pylibapogee as apg
import pylibapogee.pylibapogee_setup as SetupDevice

if len(sys.argv) < 2:
    raise RuntimeError("Requires an exposure time, in seconds, to be given")
if len(sys.argv) > 2:
    raise RuntimeError("Too many arguements given")


print("Trying to find and connect with camera")
#look for usb cameras first
devices = SetupDevice.GetUsbDevices()
print("Number of devices:", len(devices))
print("Device:", devices)
print()

# Exit if no devices
if len(devices) == 0:
    raise RuntimeError("No devices found on USB")

# Connecting to camera
cam = SetupDevice.CreateAndConnectCam(devices[0])
print(help(cam))

# Get CCD size just because
print("Imaging rows = %d, columns = %d" % ( cam.GetMaxImgRows(), cam.GetMaxImgCols()))

# Set the number of images to be made
cam.SetImageCount(1)

cam.SetCooler(True)

# Assign an exposure time.  Passed in values are to be assumed in seconds.
try:
    exposureTime = float(sys.argv[1])
except ValueError:
    raise RuntimeError("Passed in time is not a float")
print("Exposing for %d seconds" % exposureTime)

# start the exposure
cam.StartExposure(exposureTime, True)

status = None
while status != apg.Status_ImageReady: # poll the CCD status. When ccd has an image ready we move on.
    
    status = cam.GetImagingStatus()
    if(apg.Status_ConnectionError == status or
        apg.Status_DataError == status or
        apg.Status_PatternError == status ):
        msg = "Run %s: FAILED - error in camera status = %d" % (runStr, status)
        raise RuntimeError(msg)

# Get the actual image data. This gets grabbed as a numpy.ndarray
print("Getting image")
data = cam.GetImage()
print(type(data), data.shape)

# Reshape data to be an image and set up fits file
data = data.reshape(2048, 2048)
print("New data shape:", data.shape)
hdu = fits.PrimaryHDU(data, do_not_scale_image_data=True, uint=True)

print("Saving image to file")
timestr = ("%.1f"% exposureTime).replace(".", "-")
imgName = "singleExposure_%ssec.fits" % timestr

hdu.writeto(imgName, clobber=True)

# Close camera connection
cam.CloseConnection()

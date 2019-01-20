from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
)
import io
import time
import picamera
import numpy as np
from numpy.lib.stride_tricks import as_strided
from time import sleep
import csv
from fractions import Fraction



stream = io.BytesIO()
with picamera.PiCamera() as camera:
    # Let the camera warm up for a couple of seconds
    time.sleep(2)
    camera.exposure_mode = 'off'
    camera.framerate = 2
    camera.iso = 200
    camera.shutter_speed = 500000
    time.sleep(8)
    # Capture the image, including the Bayer data
    camera.capture(stream, format='jpeg', bayer=True)
    print(camera.exif_tags['IFD0.Model'])
    ver = {
        'RP_ov5647': 1,
        "RP_imx219": 2,
        }[camera.exif_tags['IFD0.Model']]
# Extract the raw Bayer data from the end of the stream, check the
# header and strip if off before converting the data into a numpy array
offset ={
        1: 6404096,
        2: 10270208,
        }[ver]
data = stream.getvalue()[-offset:]

assert data[:4] == b'BRCM'
data = data[32768:]
data = np.fromstring(data, dtype=np.uint8)\
       
# For the V2 module, the data consists of 2480 rows of 4128 bytes of data.
# There's actually 2464 rows of data, but the sensor's raw size is 2466
# rows, rounded up to the nearest multiple of 16: 2480.
#
# Likewise, the last few bytes of each row are unused (why?). Here we
# reshape the data and strip off the unused bytes.
reshape, crop = {
    1: ((1952, 3264), (1944, 3240)),
    2: ((2480, 4128), (2464, 4100)),
    }[ver]
data = data.reshape(reshape)[:crop[0], :crop[1]]
# Horizontally, each row consists of 10-bit values. Every four bytes are
# the high 8-bits of four values, and the 5th byte contains the packed low
# 2-bits of the preceding four values. In other words, the bits of the
# values A, B, C, D and arranged like so:
#
# byte 1 byte 2 byte 3 byte 4 byte 5
# AAAAAAAA BBBBBBBB CCCCCCCC DDDDDDDD AABBCCDD
#
# Here, we convert our data into a 16-bit array, shift all values left by
# 2-bits and unpack the low-order bits from every 5th byte in each row,
# then remove the columns containing the packed bits
data = data.astype(np.uint16) << 2
for byte in range(4):
    data[:, byte::5] |= ((data[:, 4::5] >> ((4 - byte) * 2)) & 0b11)
data = np.delete(data, np.s_[4::5], 1)
# Now to split the data up into its red, green, and blue components. The
# Bayer pattern of the OV5647 sensor is BGGR. In other words the first
# row contains alternating green/blue elements, the second row contains
# alternating red/green elements, and so on as illustrated below:
#
# GBGBGBGBGBGBGB
# RGRGRGRGRGRGRG
# GBGBGBGBGBGBGB
# RGRGRGRGRGRGRG
#
# Please note that if you use vflip or hflip to change the orientation
# of the capture, you must flip the Bayer pattern accordingly
rgb = np.zeros(data.shape + (3,), dtype=data.dtype)
rgb[1::2, 0::2, 0] = data[1::2, 0::2]  # Red
rgb[0::2, 0::2, 1] = data[0::2, 0::2]  # Green
rgb[1::2, 1::2, 1] = data[1::2, 1::2]  # Green
rgb[0::2, 1::2, 2] = data[0::2, 1::2]  # Blue
print("Image taken")
myfile = open('/home/pi/Desktop/FirstPlant.jpg', 'wb')

camera = picamera.PiCamera()
camera.resolution= (3280,2464)
camera.start_preview()
sleep(2)

camera.iso = 800
camera.framerate = 2
camera.shutter_speed = 500000

camera.iso = 800
time.sleep(8)
camera.capture(myfile)
myfile.close()

red_bayer = open('/home/pi/Desktop/FirstPlant_red.csv', 'w')
blue_bayer = open('/home/pi/Desktop/FirstPlant_blue.csv', 'w')
green_bayer = open('/home/pi/Desktop/FirstPlant_green.csv', 'w')
writer = csv.writer(red_bayer, delimiter= ',', quoting=csv.QUOTE_MINIMAL)
for row in rgb[1::2, 0::2, 0]:
    writer.writerow(row)
red_bayer.close
print("red saved")
writer = csv.writer(green_bayer, delimiter= ',', quoting=csv.QUOTE_MINIMAL)
for row in rgb[0::2, 0::2, 1]:
    writer.writerow(row)
green_bayer.close
print("greem saved")
writer = csv.writer(blue_bayer, delimiter= ',', quoting=csv.QUOTE_MINIMAL)
for row in rgb[0::2, 1::2, 2]:
    writer.writerow(row)
blue_bayer.close
print("blue saved")

myfile = open('/home/pi/Desktop/FirstPlant.jpg', 'wb')
'''
camera = picamera.PiCamera()
camera.resolution= (3280,2464)
camera.start_preview()
sleep(2)
camera.exposure_mode = 'off'
camera.framerate = 2
camera.iso = 200
camera.shutter_speed = 500000
time.sleep(8)
camera.capture(myfile)
myfile.close()
'''



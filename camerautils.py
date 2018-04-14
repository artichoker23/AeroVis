# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
from fractions import Fraction

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution= (3000,2000) # Callign the exact resolution throws a buffer error, round down to the nearest hundred
camera.framerate= (8)
rawCapture = PiRGBArray(camera)

#camera.framerate = 2
camera.iso = 100
time.sleep(2)
camera.shutter_speed = 75000
camera.exposure_mode = 'off'
time.sleep(15)
# allow the camera to warmup
time.sleep(0.1)

# grab an image from the camera
camera.capture(rawCapture, format="bgr")
image = rawCapture.array
compresstion_factor = int(0)
cv2.imwrite("/home/pi/Documents/OpenCVplant_succulent.png", image)

# display the image on screen and wait for a keypress
cv2.imshow("Image", image)
cv2.waitKey(0)

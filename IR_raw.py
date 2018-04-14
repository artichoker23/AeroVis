from picamera import PiCamera
from picamera import array
import time
import numpy as np
import sys



with PiCamera() as camera:
        camera.resolution=(1920,1080)
        camera.start_preview()
        time.sleep(2)
        save = '/Home/pi/Desktop/bayer.png'
        camera.capture('/home/pi/Desktop/bayer.jpg')
        camera.stop_preview
   

#with PiCamera() as camera:
  #  camera.resolution = [2529, 1944]
    #time.sleep(2)
    #image = np.empty((2560 , 1952, 3),dtype=np.uint8)
    #camera.capture(image, 'raw')
    #image = image[:2529, :1944]
    #print(image[0])

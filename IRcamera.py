import time
import picamera
import picamera.array
import numpy as np
from time import strftime
import os
import io
import csv
import json
import subprocess
from threading import Thread


class IRcamera():

    def __init__(self):
        self.save_dir = self.make_save_dir()

        self.camera = picamera.PiCamera()
        self.camera.resolution = (3280, 2464)
        self.camera.led = False
        self.enable_AE()
        self.AE= True

        self.camera_resolution = self.camera.resolution
        self.shutter_speed = 0
        self.exposure_speed = self.camera.exposure_speed  # Can read AE setting with camera.shutter_speed = 0
        self.framerate = self.camera.framerate

        self.iso = self.camera.iso
        self.analog_gain = self.camera.analog_gain
        self.digital_gain = self.camera.digital_gain


    def enable_AE(self):
        """
        Enables AE for picamera, You can read AE values by querying camera.exposure_speed and camera.iso

        :return:
        """
        self.camera.shutter_speed = 0  # Sets Picamera to AE mode
        self.camera.iso = 0
        self.camera.exposure_mode = 'auto'
        self.AE = True

    
    def update_AE(self):
        self.exposure_speed = self.camera.exposure_speed  # Can read AE setting with camera.shutter_speed = 0
        self.framerate = self.camera.framerate

        self.iso = self.camera.iso
        self.analog_gain = self.camera.analog_gain
        self.digital_gain = self.camera.digital_gain
    
    def get_bayer(self, in_image):
        """
        Takes in JPEG snapshot from Picamera with Bayer set to TRUE and parses bayer data from header

        :param in_image:
        :return 4D RGGB bayer data:
        """

        data = in_image.getvalue()[-10270208:]
        assert data[:4] == b'BRCM'
        data = data[32768:]
        data = np.fromstring(data, dtype=np.uint8)

        reshape = (2480, 4128)  # Hard coded for IMX219
        crop = (2464, 4100)

        data = data.reshape(reshape)[:crop[0], :crop[1]]

        data = data.astype(np.uint16) << 2
        for byte in range(4):
            data[:, byte::5] |= ((data[:, 4::5] >> ((4 - byte) * 2)) & 0b11)
        data = np.delete(data, np.s_[4::5], 1)

        rgb = [[], [], [], []]

        rgb[0] = data[1::2, 0::2]  # Red
        rgb[1] = data[0::2, 0::2]  # Green
        rgb[2] = data[1::2, 1::2]  # Green
        rgb[3] = data[0::2, 1::2]  # Blue

        return rgb

    def set_shutter_speed(self, shutter_speed):
        """
        TODO: Check values and set limits, add frame_rate adjuster

        will be limited by framerate, i.e. if FPS is 1/30 than fastest SS is 33ms


        :param shutter_speed:
        :return:
        """
        self.camera.shutter_speed = int((shutter_speed) * 1000000)
        self.shutter_speed = shutter_speed

    def set_framerate(self, framerate):
        """

        :param framerate, in FPS:
        :return:
        """

        self.camera.framerate = (1, int(framerate))
        self.framerate = self.camera.framerate

    def set_iso(self, gain):
        """
        TODO: Check values and set limits
        will set iso closest to [100, 200, 320, 400, 500, 640, 800]
        :param gain:
        :return:
        """
        self.camera.gain(int(gain))
        self.iso = gain

    def csv_bayer(self, bayer_data):
        """
        Takes in bayer data parsed from JPEG header output from self.get_bayer

        :param bayer_data:
        :return:
        """
        #print(len(bayer_data[0]))
        #bayer_data = bayer_data.tolist()
        bayer_order = {'red': bayer_data[0].tolist(),
                       'green1':bayer_data[1].tolist(),
                       'green2': bayer_data[2].tolist(),
                       'blue':bayer_data[3].tolist()}
        def save_bayer():
            self.savejson(bayer_order, os.path.join(self.save_dir, self.get_timestamp() + '_bayer.json'))
            
        t = Thread(target=save_bayer)
        t.start()
        #for i in range(len(bayer_data)):
         #   save_csv = os.path.join(self.save_dir, self.get_timestamp() + '_{}.csv'.format(bayer_order[i]))
          #  self.write_csv(save_csv, bayer_data[i])
            

    def capture_bayer(self, shutter_speed=0, iso=0):

        thumbnail = open(os.path.join(self.save_dir, self.get_timestamp() + '.jpg'), 'wb')

        if not self.AE:
            self.set_iso(iso)
            self.set_shutter_speed(shutter_speed)

        self.camera.capture(thumbnail)

        stream = io.BytesIO()
        self.camera.capture(stream, 'jpeg', bayer=True)
        self.csv_bayer(self.get_bayer(stream))
        stream.close()
    
    @staticmethod
    def savejson(jdict, jout):
        with open(jout, 'w') as jf:
            json.dump(jdict, jf, indent=4)
        
    @staticmethod
    def make_save_dir():
        save_dir = os.path.expanduser('~/Documents/{}'.format(strftime('%Y%m%d_%H%M%S')))

        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        return save_dir

    @staticmethod
    def write_csv(file_in, in_data):
        with open(file_in, 'w') as f:
            writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            for row in in_data:
                writer.writerow(row)

    @staticmethod
    def get_timestamp():
        return strftime('%Y%m%d_%H%M%S')

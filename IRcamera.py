import picamera
import picamera.array
import numpy as np
from time import strftime, sleep
import os
import io
import csv
import json
from threading import Thread
import imageio


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
        self.digital_gain = float(self.camera.digital_gain)


    def enable_AE(self):
        """
        Enables AE for picamera, You can read AE values by querying camera.exposure_speed and camera.iso

        :return:
        """
        self.camera.shutter_speed = 0  # Sets Picamera to AE mode
        self.camera.iso = 0
        self.camera.exposure_mode = 'auto'
        self.AE = True

    def prime_AE(self):
        if not self.AE:
            self.enable_AE()

        if self.exposure_speed == 0:
            self.camera.start_preview()
            sleep(2)
            self.camera.stop_preview()

    def update_AE(self):

        self.prime_AE()

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

        bayer_order = {'red': bayer_data[0].tolist(),
                       'green1': bayer_data[1].tolist(),
                       'green2': bayer_data[2].tolist(),
                       'blue':bayer_data[3].tolist()}
        def save_bayer():
            self.savejson(bayer_order, os.path.join(self.save_dir, self.get_timestamp() + '_bayer.json'))
            
        t = Thread(target=save_bayer)
        t.start()

    def snapshot(self, save=False, im_name=None):

        if not save:
            stream = io.BytesIO()
            self.camera.capture(stream, 'jpeg',)
            stream.close()
        else:
            thumbnail = open(im_name, 'wb')
            self.camera.capture(thumbnail)

    def capture_bayer(self, shutter_speed=0, iso=0):

        

        if not self.AE:
            self.set_iso(iso)
            self.set_shutter_speed(shutter_speed)

        #self.snapshot(save=True, im_name=thumbnail)

        stream = io.BytesIO()
        self.camera.capture(stream, 'jpeg', bayer=True)
        bayer_arr = self.get_bayer(stream)

        stream.close()

        IR_png = os.path.join(self.save_dir, '{}_IR.png'.format(self.get_timestamp()))
        blue_png = os.path.join(self.save_dir, '{}_Blue.png'.format(self.get_timestamp()))
        
        IRthumb_png = os.path.join(self.save_dir, '{}_IR_thumb.png'.format(self.get_timestamp()))
        bluethumb_png = os.path.join(self.save_dir, '{}_Blue_thumb.png'.format(self.get_timestamp()))

        IR_t = Thread(target=self.save_png16, args=(bayer_arr[0], IR_png))
        blue_t = Thread(target=self.save_png16, args=(bayer_arr[3], blue_png))
        
        IRthumb_t = Thread(target=self.save_corr_png8, args=(bayer_arr[0], IRthumb_png))
        bluethumb_t = Thread(target=self.save_corr_png8, args=(bayer_arr[3], bluethumb_png))

        IR_t.start()
        blue_t.start()
        
        IRthumb_t.start()
        bluethumb_t.start()

    def save_png16(self, in_arr, out_png):
        if not out_png.endswith('.png'):
            out_png += '.png'
             
        imageio.imsave(out_png, self.convert10to16(in_arr).astype(np.uint16))
        
    
    def save_corr_png8(self, in_arr, out_png):
        if not out_png.endswith('.png'):
            out_png += '.png'
        
        im_16 = self.convert10to16(in_arr)
        
        basic_corr = (im_16 - 4100) ** 2.2
             
        imageio.imsave(out_png, in_arr.astype(np.uint8))
    
    
    @staticmethod
    def savejson(jdict, jout):
        with open(jout, 'w') as jf:
            json.dump(jdict, jf, indent=4)

    @staticmethod
    def convert10to16(in_arr):
        arr_16 = in_arr * ( 2**16 / 1023. )

        return arr_16
        
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

from IRcamera import IRcamera
from time import sleep


def main():
    interval = 30
    captures = 10
    IRc = IRcamera()

    for i in range(captures):
        IRc.update_AE()
        IRc.set_framerate(1)
        print('------- Capturing -------')
        print(' Shutter Speed: {}'.format(IRc.exposure_speed))
        print(' Framerate: {}'.format(IRc.framerate))
        print(' ISO: {}'.format(IRc.iso))
        print(' Analog Gain: {}'.format(IRc.analog_gain))
        print(' Digital Gain: {}'.format(IRc.digital_gain))

        IRc.capture_bayer()

        print('-------------------------\n')
        sleep(interval)



if __name__ == '__main__':
    main()
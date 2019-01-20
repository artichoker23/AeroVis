from IRcamera import IRcamera
from time import sleep


def main():
    interval = 30
    captures = 10
    IRc = IRcamera()

    for i in range(captures):
        print('------- Capturing -------')
        print(' Shutter Speed: {}'.format(IRc.exposure_speed))
        print(' ISO: {}'.format(IRc.iso))
        print(' Analog Gain: {}'.format(IRc.analog_gain))
        print(' Digital Gain: {}'.format(IRc.digital_gain))

        IRcamera.capture_bayer()

        print('----------------------')
        sleep(interval)



if __name__ == '__main__':
    main()
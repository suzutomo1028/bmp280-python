#!/usr/bin/env python3

import sys, os
sys.path.append(os.pardir)
from sc18im700 import SC18IM700
from bmp280 import BMP280
import time

def main():
    with SC18IM700('COM4') as sc18:
        bmp280 = BMP280(sc18)
        bmp280.begin()
        bmp280.normal_mode()
        try:
            while True:
                temp_C, press_Pa = bmp280.get_measure_data()
                print('{:.2f} degC / {:.2f} hPa'.format(temp_C, press_Pa/100))
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()

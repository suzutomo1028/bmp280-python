#!/usr/bin/env python3

import sys, os
sys.path.append(os.pardir)
from sc18im700 import SC18IM700
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s : %(module)s : %(funcName)s : %(message)s')

BMP280_I2C_ADDR = 0x76

CALIB      = 0x88
ID         = 0xD0
RESET      = 0xE0
STATUS     = 0xF3
CTRL_MEAS  = 0xF4
CONFIG     = 0xF5
PRESS_MSB  = 0xF7
PRESS_LSB  = 0xF8
PRESS_XLSB = 0xF9
TEMP_MSB   = 0xFA
TEMP_LSB   = 0xFB
TEMP_XLSB  = 0xFC

CHIP_ID    = 0x58
RESET_CODE = 0xB6

OSRS_T_SKIPPED = 0b000
OSRS_T_X1      = 0b001
OSRS_T_X2      = 0b010
OSRS_T_X4      = 0b011
OSRS_T_X8      = 0b100
OSRS_T_X16     = 0b101

OSRS_P_SKIPPED = 0b000
OSRS_P_X1      = 0b001
OSRS_P_X2      = 0b010
OSRS_P_X4      = 0b011
OSRS_P_X8      = 0b100
OSRS_P_X16     = 0b101

SLEEP_MODE  = 0b00
FORCED_MODE = 0b01
NORMAL_MODE = 0b11

T_SB_05   = 0b000
T_SB_625  = 0b001
T_SB_125  = 0b010
T_SB_250  = 0b011
T_SB_500  = 0b100
T_SB_1000 = 0b101
T_SB_2000 = 0b110
T_SB_4000 = 0b111

FILTER_OFF = 0b000
FILTER_2   = 0b001
FILTER_4   = 0b010
FILTER_8   = 0b011
FILTER_16  = 0b100

class BMP280:
    """ 圧力センサー（BMP280）の制御ドライバ """ 

    def __init__(self, sc18: SC18IM700) -> None:
        """ インスタンスを初期化する
        """
        self.sc18: SC18IM700 = sc18
        self.dig_T1: int = None
        self.dig_T2: int = None
        self.dig_T3: int = None
        self.dig_P1: int = None
        self.dig_P2: int = None
        self.dig_P3: int = None
        self.dig_P4: int = None
        self.dig_P5: int = None
        self.dig_P6: int = None
        self.dig_P7: int = None
        self.dig_P8: int = None
        self.dig_P9: int = None
        self.t_fine: int = None

    def begin(self) -> None:
        """ デバイスを開始する
        """
        self.write_reset()
        self.read_calib()
        self.write_config(T_SB_05, FILTER_OFF, False)
        self.write_ctrl_meas(OSRS_T_X1, OSRS_P_X1, SLEEP_MODE)

    def read_calib(self) -> None:
        """ 調整パラメータを読み込む
        """
        wdata = bytes([CALIB])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=24)
        self.dig_T1 = int.from_bytes(rdata[ 0: 2], byteorder='little', signed=False)
        self.dig_T2 = int.from_bytes(rdata[ 2: 4], byteorder='little', signed=True)
        self.dig_T3 = int.from_bytes(rdata[ 4: 6], byteorder='little', signed=True)
        self.dig_P1 = int.from_bytes(rdata[ 6: 8], byteorder='little', signed=False)
        self.dig_P2 = int.from_bytes(rdata[ 8:10], byteorder='little', signed=True)
        self.dig_P3 = int.from_bytes(rdata[10:12], byteorder='little', signed=True)
        self.dig_P4 = int.from_bytes(rdata[12:14], byteorder='little', signed=True)
        self.dig_P5 = int.from_bytes(rdata[14:16], byteorder='little', signed=True)
        self.dig_P6 = int.from_bytes(rdata[16:18], byteorder='little', signed=True)
        self.dig_P7 = int.from_bytes(rdata[18:20], byteorder='little', signed=True)
        self.dig_P8 = int.from_bytes(rdata[20:22], byteorder='little', signed=True)
        self.dig_P9 = int.from_bytes(rdata[22:24], byteorder='little', signed=True)

    def read_id(self) -> int:
        """ チップIDを読み込む
        """
        wdata = bytes([ID])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=1)
        value = int.from_bytes(rdata, byteorder='big')
        return value

    def write_reset(self) -> None:
        """ デバイスをリセットする
        """
        wdata = bytes([RESET]) + bytes([RESET_CODE])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(1)

    def read_status(self) -> tuple[bool, bool]:
        """ ステータスを読み込む
        """
        wdata = bytes([STATUS])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=1)
        value = int.from_bytes(rdata, byteorder='big')
        measuring = bool(value & 0x08)
        im_update = bool(value & 0x01)
        return measuring, im_update

    @property
    def is_measuring(self) -> bool:
        """ 測定中のとき True を返す
        """
        measuring, im_update = self.read_status()
        return measuring

    @property
    def is_im_update(self) -> bool:
        """ NVMからデータコピー中のとき True を返す
        """
        measuring, im_update = self.read_status()
        return im_update

    def read_ctrl_meas(self) -> tuple[int, int, int]:
        """ 制御レジスタから値を読み込む
        """
        wdata = bytes([CTRL_MEAS])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=1)
        value = int.from_bytes(rdata, byteorder='big')
        osrs_t = int((value & 0xE0) >> 5)
        osrs_p = int((value & 0x1C) >> 2)
        mode   = int((value & 0x03) >> 0)
        return osrs_t, osrs_p, mode

    def write_ctrl_meas(self, osrs_t: int, osrs_p: int, mode: int) -> None:
        """ 制御レジスタへ値を書き込む
        """
        if (osrs_t < 0) or (7 < osrs_t):
            raise ValueError
        if (osrs_p < 0) or (7 < osrs_p):
            raise ValueError
        if (mode < 0) or (3 < mode):
            raise ValueError
        value = int((osrs_p << 5) | (osrs_p << 2) | (mode << 0))
        wdata = bytes([CTRL_MEAS]) + bytes([value])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)

    def sleep_mode(self) -> None:
        """ スリープモードに遷移する
        """
        osrs_t, osrs_p, mode = self.read_ctrl_meas()
        mode = SLEEP_MODE
        self.write_ctrl_meas(osrs_t, osrs_p, mode)

    def forced_mode(self) -> None:
        """ 強制モードに遷移する
        """
        osrs_t, osrs_p, mode = self.read_ctrl_meas()
        mode = FORCED_MODE
        self.write_ctrl_meas(osrs_t, osrs_p, mode)

    def normal_mode(self) -> None:
        """ 通常モードに遷移する
        """
        osrs_t, osrs_p, mode = self.read_ctrl_meas()
        mode = NORMAL_MODE
        self.write_ctrl_meas(osrs_t, osrs_p, mode)

    def read_config(self) -> tuple[int, int, bool]:
        """ 設定レジスタから値を読み込む
        """
        wdata = bytes([CONFIG])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=1)
        value = int.from_bytes(rdata, byteorder='big')
        t_sb     = int((value & 0xE0) >> 5)
        filter   = int((value & 0x1C) >> 2)
        spi3w_en = int((value & 0x01) >> 0)
        return t_sb, filter, spi3w_en

    def write_config(self, t_sb: int, filter: int, spi3w_en: bool) -> None:
        """ 設定レジスタへ値を書き込む
        """
        if (t_sb < 0) or (7 < t_sb):
            raise ValueError
        if (filter < 0) or (7 < filter):
            raise ValueError
        value = int((t_sb << 5) | (filter << 2) | (int(spi3w_en) << 0))
        wdata = bytes([CONFIG]) + bytes([value])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)

    def read_press(self) -> int:
        """ 圧力の測定値を読み込む
        """
        wdata = bytes([PRESS_MSB])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=3)
        value = int.from_bytes(rdata, byteorder='big')
        return int((value & 0xFFFFF0) >> 4)

    def read_temp(self) -> int:
        """ 温度の測定値を読み込む
        """
        wdata = bytes([TEMP_MSB])
        self.sc18.write_i2c(BMP280_I2C_ADDR, wdata)
        time.sleep(10/1000)
        rdata = self.sc18.read_i2c(BMP280_I2C_ADDR, size=3)
        value = int.from_bytes(rdata, byteorder='big')
        return int((value & 0xFFFFF0) >> 4)

    def compensate_temp(self, raw_temp: int) -> float:
        """ 温度測定値を補正する
        """
        var1 = ((((raw_temp >> 3) - (self.dig_T1 << 1))) * (self.dig_T2)) >> 11
        var2 = (((((raw_temp >> 4) - (self.dig_T1)) * ((raw_temp >> 4) - (self.dig_T1))) >> 12) * (self.dig_T3)) >> 14
        self.t_fine = var1 + var2
        temp = (self.t_fine * 5 + 128) >> 8
        return float(temp / 100)

    def compensate_press(self, raw_press: int) -> float:
        """ 圧力測定値を補正する
        """
        # raw_temp = self.read_temp()
        # self.compensate_temp(raw_temp)
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = ((((1 << 47) + var1)) * self.dig_P1) >> 33
        if var1 == 0:
            press = 0
        else:
            press = 1048576 - raw_press
            press = int((((press << 31) - var2) * 3125) / var1)
            var1 = (self.dig_P9 * (press >> 13) * (press >> 13)) >> 25
            var2 = (self.dig_P8 * press) >> 19
            press = ((press + var1 + var2) >> 8) + (self.dig_P7 << 4)
        return float(press / 256)

    def get_measure_data(self) -> tuple[float, float]:
        """ 測定データを取得する
        """
        raw_temp = self.read_temp()
        raw_press = self.read_press()
        temp_C = self.compensate_temp(raw_temp)
        press_Pa = self.compensate_press(raw_press)
        return temp_C, press_Pa

if __name__ == '__main__':
    pass

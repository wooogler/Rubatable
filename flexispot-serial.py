import lgpio as GPIO
import serial
import time

# Serial 포트 설정 (SERIAL_PORT를 실제 포트 이름으로 변경)
SERIAL_PORT = "/dev/ttyAMA0"  # 예시로 ttyS0 사용, 실제 포트 확인 필요
PIN_20 = 20

SUPPORTED_COMMANDS = {
    "up": bytearray(b'\x9b\x06\x02\x01\x00\xfc\xa0\x9d'),
    "down": bytearray(b'\x9b\x06\x02\x02\x00\x0c\xa0\x9d'),
    "m": bytearray(b'\x9b\x06\x02\x20\x00\xac\xb8\x9d'),
    "wake_up": bytearray(b'\x9b\x06\x02\x00\x00\x6c\xa1\x9d'),
    "preset_1": bytearray(b'\x9b\x06\x02\x04\x00\xac\xa3\x9d'),
    "preset_2": bytearray(b'\x9b\x06\x02\x08\x00\xac\xa6\x9d'),
    "preset_3": bytearray(b'\x9b\x06\x02\x10\x00\xac\xac\x9d'),
    "preset_4": bytearray(b'\x9b\x06\x02\x00\x01\xac\x60\x9d'),
}

class LoctekMotion():
    def __init__(self, serial, pin_20):
        self.serial = serial
        self.h = GPIO.gpiochip_open(0)
        GPIO.gpio_claim_output(self.h, pin_20)
        GPIO.gpio_write(self.h, pin_20, 1)

    def decode_seven_segment(self, byte):
        binaryByte = bin(byte).replace("0b","").zfill(8)
        decimal = False
        if binaryByte[0] == "1":
            decimal = True
        if binaryByte[1:] == "0111111":
            return 0, decimal
        if binaryByte[1:] == "0000110":
            return 1, decimal
        if binaryByte[1:] == "1011011":
            return 2, decimal
        if binaryByte[1:] == "1001111":
            return 3, decimal
        if binaryByte[1:] == "1100110":
            return 4, decimal
        if binaryByte[1:] == "1101101":
            return 5, decimal
        if binaryByte[1:] == "1111101":
            return 6, decimal
        if binaryByte[1:] == "0000111":
            return 7, decimal
        if binaryByte[1:] == "1111111":
            return 8, decimal
        if binaryByte[1:] == "1101111":
            return 9, decimal
        if binaryByte[1:] == "1000000":
            return 10, decimal
        return -1, decimal

    def current_height(self):
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        time.sleep(0.1)
        history = [None] * 5
        msg_type = 0
        msg_len = 0
        valid = False
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                data = self.serial.read(1)
                if history[0] == 0x9b:
                    msg_len = data[0]
                if history[1] == 0x9b:
                    msg_type = data[0]
                if history[2] == 0x9b:
                    if msg_type == 0x12 and msg_len == 7:
                        if data[0] == 0:
                            print("height is empty                ", end='\r')
                        else:
                            valid = True
                if history[3] == 0x9b:
                    if valid == True:
                         pass
                if history[4] == 0x9b:
                    if valid == True and msg_len == 7:
                        height1, decimal1 = self.decode_seven_segment(history[1])
                        height1 = height1 * 100
                        height2, decimal2 = self.decode_seven_segment(history[0])
                        height2 = height2 * 10
                        height3, decimal3 = self.decode_seven_segment(data[0])
                        if height1 < 0 or height2 < 0 or height3 < 0:
                            # print("Display Empty","          ",end='\r')
                            print("Display Empty")
                            return None
                        else:
                            finalHeight = height1 + height2 + height3
                            decimal = decimal1 or decimal2 or decimal3
                            if decimal == True:
                                finalHeight = finalHeight / 10
                            # print("Height:", finalHeight, "       ", end='\r')
                            print("Height:", finalHeight)
                            return finalHeight
                history[4] = history[3]
                history[3] = history[2]
                history[2] = history[1]
                history[1] = history[0]
                history[0] = data[0]
                
            except Exception as e:
                print('cannot get height', e)
                return None
        print('Timeout while getting height')
        return None

def main():
    try: 
        ser = serial.Serial(SERIAL_PORT, 9600, timeout=5)
        loctek = LoctekMotion(ser, PIN_20)
        loctek.current_height()
    except serial.SerialException as e:
        print(f"Serial connection failed: {e}")
    finally:
        GPIO.gpiochip_close(loctek.h)
    
if __name__ == "__main__":
    main()

        

import serial
import lgpio as GPIO
import sys
import time
import threading

SERIAL_PORT = "/dev/ttyAMA0" 
relay_1 = 17
relay_2 = 27

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

    def __init__(self, serial):
        """Initialize LoctekMotion"""
        self.serial = serial
        self.get_current_height_timeout = 3
        self.get_height_when_sleep_timeout = 3
        self.stop_event = threading.Event()
        self.height_event = threading.Event()

        # GPIO 핀 번호 설정
        self.h = GPIO.gpiochip_open(0)
        GPIO.gpio_claim_output(self.h, relay_1)
        GPIO.gpio_claim_output(self.h, relay_2)
        GPIO.gpio_write(self.h, relay_1, 0)
        GPIO.gpio_write(self.h, relay_2, 0)

        self.is_moving = False
        self.current_height_value = None
    def execute_command(self, command_name: str):
        """Execute command"""
        command = SUPPORTED_COMMANDS.get(command_name)

        if not command:
            raise Exception("Command not found")

        self.serial.write(command)

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
        while time.time() - start_time < self.get_current_height_timeout:
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
    
    def read_height_thread(self):
        while not self.height_event.is_set():
            height = self.current_height()
            if height is not None:
                print(f"current height: {height} inch")
                self.current_height_value = height
            else:
                print("cannot get current height")
            time.sleep(0.1)

    def move(self, command_name: str):
        """Move the desk"""
        print(f"Starting move: {command_name}")
        command = SUPPORTED_COMMANDS.get(command_name)

        if not command:
            raise Exception("Command not found")

        if command_name in ["up", "down"]:
            self.is_moving = True
            self.stop_event.clear()
            self.height_event.clear()

            GPIO.gpio_write(self.h, relay_1, 1)
            GPIO.gpio_write(self.h, relay_2, 1)

            height_thread = threading.Thread(target=self.read_height_thread)
            height_thread.start()
            
            try:
                while self.is_moving:
                    if self.stop_event.is_set():
                        break
                    self.execute_command(command_name)
                    time.sleep(0.5)
            finally:
                self.height_event.set()
                height_thread.join()
                
        elif command_name == "stop":
            self.stop()
        else:
            self.execute_command(command_name)
        print("Exiting move")

    def stop(self):
        """Stop the desk movement"""
        print("Stopping desk movement")
        self.is_moving = False
        self.stop_event.set()

        GPIO.gpio_write(self.h, relay_1, 0)
        GPIO.gpio_write(self.h, relay_2, 0)

        #책상을 멈춘 후 잠시 대기
        time.sleep(1)  # 필요에 따라 시간을 조절하세요

        # 최종 높이 가져오기
        final_height = self.current_height()
        if final_height is not None:
            print(f"final height: {final_height} inch")
        else:
            print("최종 높이를 가져올 수 없습니다.")

        time.sleep(1)

    def get_height_when_sleep(self, check: bool = True):
        GPIO.gpio_write(self.h, relay_1, 1)
        GPIO.gpio_write(self.h, relay_2, 1)
        current_time = time.time()
        while time.time() - current_time < self.get_height_when_sleep_timeout:
            time.sleep(0.5)
            self.execute_command("preset_4")
            height = self.current_height()
            if height is not None:
                print(f"get_height_when_sleep: {height} inch")
                break
            else:
                print("cannot get height, retrying...")

        if check:
            time.sleep(0.5)
            GPIO.gpio_write(self.h, relay_1, 0)
            GPIO.gpio_write(self.h, relay_2, 0)

        return height
        

    def move_to_height(self, target_height: float):
        """Move the desk to a specific height"""
        print(f"Moving to target height: {target_height} inch")
        self.is_moving = True
        self.stop_event.clear()
        self.height_event.clear()

        GPIO.gpio_write(self.h, relay_1, 1)
        GPIO.gpio_write(self.h, relay_2, 1)

        height_thread = threading.Thread(target=self.read_height_thread)
        height_thread.start()

        time.sleep(0.5)

        try:
            while self.is_moving:
                current_height = self.current_height_value
                if current_height is None:
                    current_height = self.get_height_when_sleep(check=False)
                    time.sleep(1)
                    if current_height is None:
                        print("최종 높이를 가져올 수 없습니다.")
                        self.stop()
                        break
                

                if abs(current_height - target_height) < 0.5:  # 목표 높이에 도달하면 멈춤
                    print(f"stop move to target height")
                    self.stop()
                    break

                if current_height < target_height:
                    time.sleep(0.5)
                    self.execute_command("up")
                else:
                    time.sleep(0.5)
                    self.execute_command("down")

        finally:
            self.height_event.set()
            height_thread.join()

        print("Exiting move to height")

def main():
    try:
        command = sys.argv[1]
        ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
        locktek = LoctekMotion(ser)
        locktek.execute_command("wake_up")
        locktek.move(command)
    except serial.SerialException as e:
        print(e)
        return
    # Error handling for command line arguments
    except IndexError:
        program = sys.argv[0]
        print("Usage: python3",program,"[COMMAND]")
        print("Supported Commands:")
        for command in SUPPORTED_COMMANDS:
            print("\t", command)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        print("the end of the program")
        GPIO.gpiochip_close(locktek.h)

if __name__ == "__main__":
    main()

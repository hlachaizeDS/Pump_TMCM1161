import math
import struct
import time
from serial import *
import sys

MSG_STRUCTURE = ">BBBBiB"
REPLY_STRUCTURE = ">BBBBiB"
REPLY_LENGTH = 9

class DispenseUnit_1161:
    '''
    To use for pumps with TMCM-1161 card
    '''

    def __init__(self,parent,serial,address,motor_id=0):

        self.parent=parent

        self.serial=serial
        self.address=address
        self.motor_id = motor_id # with TMCM-1161, will always be 0 since only 1 axis card


        #hardware parameters
        self.microsteps = 2 ** 4
        self.dist_per_full_step = 0.0254  # mm
        self.radius = 4.6 / 2 #mm
        self.max_disp = 200  # ul

    def _binaryadd(self, address, command, type, motorbank, value): #to compute checksum
        checksum_struct = struct.pack(
            MSG_STRUCTURE[:-1], int(address), int(command), int(type), int(motorbank), int(value))
        checksum = 0
        for s in checksum_struct:
            try:
                checksum += int(s.encode('hex'), 16) % 256
            except:
                checksum += s % 256
            checksum = checksum % 256
        return int(checksum)

    def send_to_serial(self, address, command, type, motorbank, value):

        checksum = self._binaryadd(address, command, type, motorbank, value)
        msg = struct.pack(MSG_STRUCTURE, int(address), int(command),
                          int(type), int(motorbank), int(value), int(checksum))
        self.serial.write(msg)
        rep = self.serial.read(REPLY_LENGTH)
        reply = struct.unpack(REPLY_STRUCTURE, rep)
        return reply

    def ul_to_usteps(self,volume_ul):
        steps_nb = int(volume_ul * self.microsteps / (math.pi * (self.radius ** 2) * self.dist_per_full_step))
        return steps_nb

    def run_firmware_from_line(self,line):
        self.send_to_serial(self.address, 129, 1, self.motor_id, line)

    def set_global_parameter(self,parameter_number,value):
        self.send_to_serial(self.address, 9, parameter_number, 2, value)

    def get_status(self):
        #Status is
        # 0 for idle
        # 1 for busy
        # 2 for can_move
        reply = self.send_to_serial(self.address, 10, 5, 2 , 0)
        return reply[4] #corresponds to reply.value

    def wait_for_canmove(self):
        while 1:
            status=self.get_status()
            if status == 0 or status == 2:
                break
            time.sleep(0.01)

    def wait_for_idle(self):
        while 1:
            time.sleep(0.01)
            status=self.get_status()
            if status == 0:
                break

    def init(self):
        self.run_firmware_from_line(0)

    def dispense(self, volume_ul):

        full_strokes = volume_ul // self.max_disp
        additional_volume= volume_ul % self.max_disp

        if additional_volume==0 and full_strokes!=0 : #Particular case where we're a multiple of 200
            full_strokes-=1
            additional_volume=200

        additional_volume_usteps=self.ul_to_usteps(additional_volume)

        #print(full_strokes)
        #print(additional_volume)
        #print(additional_volume_usteps)
        self.set_global_parameter(1,full_strokes)
        self.set_global_parameter(0,additional_volume_usteps)

        if full_strokes==0 :
            if additional_volume <= 15:
                self.run_firmware_from_line(4)
            else:
                self.run_firmware_from_line(1)
        else:
            if additional_volume <= 15:
                self.run_firmware_from_line(5)
            else:
                self.run_firmware_from_line(3)


if __name__ == "__main__":

    serial_port = Serial("COM3", 9600)
    pump_1=DispenseUnit_1161("fakeparent",serial_port,1,0)
    #We get which mode we're inmode 0 = initialisation, mode 1 = dispense

    mode=1
    volume=150

    if mode==0:
        pump_1.init()
    elif mode==1:
        pump_1.dispense(int(volume))
        pump_1.wait_for_idle()

    serial_port.close()

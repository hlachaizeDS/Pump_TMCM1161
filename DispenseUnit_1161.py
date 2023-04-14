import pyTMCL
import math
import time
from serial import *



class DispenseUnit_1161:
    '''
    To use for pumps with TMCM-1161 card
    '''

    def __init__(self,parent,bus,address,motor_id=0):

        self.parent=parent

        self.bus=bus
        self.address=address
        self.motor_id = motor_id # with TMCM-1161, will always be 0 since only 1 axis card

        self.Motor = self.bus.get_motor(self.address,self.motor_id)
        self.MotorParamInterface =pyTMCL.motor.AxisParameterInterface(self.Motor)

        #hardware parameters
        self.microsteps = 2 ** 4
        self.dist_per_full_step = 0.0254  # mm
        self.radius = 4.6 / 2 #mm
        self.max_disp = 200  # ul

    def ul_to_usteps(self,volume_ul):
        steps_nb = int(volume_ul * self.microsteps / (math.pi * (self.radius ** 2) * self.dist_per_full_step))
        return steps_nb

    def run_firmware_from_line(self,line):
        self.bus.send(self.address, pyTMCL.Command.RUN_APPLICATION, 1, self.motor_id, line)

    def set_global_parameter(self,parameter_number,value):
        self.bus.send(self.address, pyTMCL.Command.SGP, parameter_number, 2, value)

    def get_status(self):
        #Status is
        # 0 for idle
        # 1 for busy
        # 2 for can_move
        reply = self.bus.send(self.address, pyTMCL.Command.GGP, 5, 2 , 0)
        return reply.value

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
            full_strokes -= 1
            additional_volume = 200

        additional_volume_usteps=self.ul_to_usteps(additional_volume)

        #print(full_strokes)
        #print(additional_volume)
        #print(additional_volume_usteps)
        self.set_global_parameter(1,full_strokes)
        self.set_global_parameter(0,additional_volume_usteps)

        if full_strokes==0 :
            if additional_volume <= 5:
                self.run_firmware_from_line(4)
            else:
                self.run_firmware_from_line(1)
        else:
            if additional_volume <= 5:
                self.run_firmware_from_line(5)
            else:
                self.run_firmware_from_line(3)


if __name__ == "__main__":

    serial_port = Serial('COM3', 9600)
    bus = pyTMCL.connect(serial_port)

    pump_1=DispenseUnit_1161("fakeparent",bus,1,0)

    #pump_1.init()
    pump_1.dispense(100)
    serial_port.close()
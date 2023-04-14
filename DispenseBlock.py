from DispenseUnit_1161 import *

class DispenseBlock:
    '''
    Represents a collective of pumps
    '''

    def __init__(self,parent,dus):

        self.parent=parent
        self.dus=dus #list of pumps

    def multi_dispense(self,volumes):
        #if list of volumes not at the same length as dus, we add 0s
        volumes=volumes + [0]*(len(self.dus)-len(volumes))

        self.wait_for_idle()

        for index in range(len(self.dus)):
            self.dus[index].dispense(volumes[index])

        self.wait_for_move()

    def wait_for_move(self):

        pumps_nb=len(self.dus)
        is_ok_to_move=[0]*pumps_nb

        time.sleep(0.01) #in case we just sent the command to move

        while any(is_ok_to_move)==0:
            for index in range(pumps_nb):
                if is_ok_to_move[index]==0:
                    pump_status=self.dus[index].get_status()
                    if pump_status==0 or pump_status==2:
                        is_ok_to_move[index]=1
            time.sleep(0.1)

    def wait_for_idle(self):

        pumps_nb=len(self.dus)
        is_ok_to_move=[0]*pumps_nb

        time.sleep(0.01) #in case we just sent the command to move

        while any(is_ok_to_move)==0:
            for index in range(pumps_nb):
                if is_ok_to_move[index]==0:
                    pump_status=self.dus[index].get_status()
                    if pump_status==0:
                        is_ok_to_move[index]=1
            time.sleep(0.1)



if __name__ == "__main__":

    serial_port = Serial("COM3", 9600)
    bus = pyTMCL.connect(serial_port)
    pump_1 = DispenseUnit_1161("FP", bus, 1, 0)

    disp_block = DispenseBlock("FP",[pump_1])

    disp_block.multi_dispense([200])
    disp_block.multi_dispense([200])
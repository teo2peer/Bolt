# use the PCA9685 library
import time   
from adafruit_servokit import ServoKit
import multiprocessing as mp
import numpy as np
import asyncio 


class Movment(mp.Process):
    def __init__(self, movment_pipe):
        super().__init__()

        # Pipe
        self.movment_pipe = movment_pipe

        #Constants
        self.nbPCAServo=16 

        #Parameters
        self.MIN_IMP  =[500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500]
        self.MAX_IMP  =[2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500]
        self.MIN_ANG  =[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.MAX_ANG  =[180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180]


        #Objects
        self.pca = ServoKit(channels=16)

        # init
        for i in range(self.nbPCAServo):
            self.pca.servo[i].set_pulse_width_range(self.MIN_IMP[i] , self.MAX_IMP[i])
        
        # right arm
        self.rshoulder = self.pca.servo[0]
        self.relbow = self.pca.servo[1]
        self.rarm = self.pca.servo[2]

        # left arm
        self.lshoulder = self.pca.servo[4]
        self.lelbow = self.pca.servo[5]
        self.larm = self.pca.servo[6]

        # head
        self.hyaw = self.pca.servo[8]
        self.hroll = self.pca.servo[9]
        self.hpitch = self.pca.servo[10]

        # init position
        # self.initialize_position()
        

    def run(self):
        text = "";
        while True:
            text = self.movment_pipe.recv()
            
            if text == "greetings":
                self.greetings_movment()

            elif text == "yes" or text == "afirmative":
                self.yes_head()
            
            elif text == "exit":
                break
            else:
                continue


    def initialize_position(self):
            
            self.rshoulder.angle = 180
            self.relbow.angle = 90
            self.rarm.angle = 1

            self.lshoulder.angle = 0
            self.lelbow.angle = 90
            self.larm.angle = 180

            self.hyaw.angle = 90
            self.hroll.angle = 92
            self.hpitch.angle = 90

            asyncio.run(self.move_servo(self.rshoulder, 0, 0.4))
            asyncio.run(self.move_servo(self.relbow, 180, 0.4))
            asyncio.run(self.move_servo(self.rarm, 1, 0.2))

            asyncio.run(self.move_servo(self.lshoulder, 180, 0.4))
            asyncio.run(self.move_servo(self.lelbow, 0, 0.4))
            asyncio.run(self.move_servo(self.larm, 180, 0.2))

            asyncio.run(self.move_servo(self.hyaw, 90, 0.4))
            asyncio.run(self.move_servo(self.hroll, 92, 0.4))
            asyncio.run(self.move_servo(self.hpitch, 90, 0.4))

            
            time.sleep(1)
            asyncio.run(self.swing_servo(self.relbow, 65, 105, 2,0.1))
            asyncio.run(self.swing_servo(self.lelbow, 65, 105, 2,0.1))

            # swing the head
            asyncio.run(self.swing_servo(self.hpitch, 65, 105, 2,0.1))
            asyncio.run(self.swing_servo(self.hroll, 65, 105, 2,0.1))
            asyncio.run(self.swing_servo(self.hyaw, 65, 105, 2,0.1))

            time.sleep(1)
            # move the head
            asyncio.run(self.move_servo(self.hroll, 92, 0.4))
            # move the hands to the init position
            # first elbow
            asyncio.run(self.move_servo(self.relbow, 90, 0.4))
            asyncio.run(self.move_servo(self.lelbow, 90, 0.4))
            # then shoulder
            asyncio.run(self.move_servo(self.rshoulder, 180, 0.4))
            asyncio.run(self.move_servo(self.lshoulder, 0, 0.4))
            # then arm
            asyncio.run(self.move_servo(self.rarm, 1, 0.2))
            asyncio.run(self.move_servo(self.larm, 180, 0.2))






    # arm movments

    def greetings_movment(self):

            

            asyncio.run(self.move_servo(self.rshoulder, 0, 0.5))
            asyncio.run(self.move_servo(self.relbow, 90, 0.5))
            asyncio.run(self.move_servo(self.rarm, 1, 0.3))

            # move the elbow in swing)
            asyncio.run(self.swing_servo(self.relbow, 65, 105, 5,0.2))

            asyncio.run(self.move_servo(self.rshoulder, 180, 0.5))
            asyncio.run(self.move_servo(self.relbow, 92, 0.5))
            asyncio.run(self.move_servo(self.rarm, 1, 0.3))


    

    # head movments
    def yes_head(self):
            asyncio.run(self.swing_servo(self.hpitch, 65, 105, 5,0.2))





    async def swing_servo(self, servo, angle_init, angle_end, times, speed=0.5):
            for i in range(0,times):
                await self.move_servo(servo, angle_init, 0.5)
                await self.move_servo(servo, angle_end, 0.5)
            await self.move_servo(servo, angle_init, 0.5)


    async def move_servo(self, servo, target_angle, move_time):
        # Get the current angle of the servo
        current_angle = servo.angle

        # Convert the current and target angles to pulses
        current_pulse = int(np.interp(current_angle, [0, 180], [self.MIN_IMP[1], self.MAX_IMP[1]]))
        target_pulse = int(np.interp(target_angle, [0, 180], [self.MIN_IMP[1], self.MAX_IMP[1]]))

        # Calculate the number of steps and the wait time between each step
        steps = 100
        wait_time = move_time / steps

        # Calculate the difference between the current and target pulses
        pulse_diff = (target_pulse - current_pulse) / steps

        # Move the servo to the target position
        for i in range(steps):
            # Calculate the new pulse width
            new_pulse = int(current_pulse + pulse_diff * i)

            # Move the servo to the new pulse width
            servo.angle = np.interp(new_pulse, [self.MIN_IMP[1], self.MAX_IMP[1]], [0, 180])

            # Wait for the specified time
            await asyncio.sleep(wait_time)

        # At the end of the movement, set the angle to the target angle
        servo.angle = target_angle

    




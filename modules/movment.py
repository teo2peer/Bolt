# use the PCA9685 library
import time   
from adafruit_servokit import ServoKit
import multiprocessing as mp
import numpy as np
import asyncio 
import paho.mqtt.client as mqtt
import json

class Movment(mp.Process):
    def __init__(self, movment_pipe, env_vars):
        super().__init__()

        # Pipe
        self.movment_pipe = movment_pipe

        # Environment variables
        self.env_vars = env_vars
        self.last_movment = time.time()

        #Constants
        self.nbPCAServo=16 

        #Parameters
        self.MIN_IMP  =[500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500]
        self.MAX_IMP  =[2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500]
        self.MIN_ANG  =[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.MAX_ANG  =[180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180, 180]


        self.move_list_words= ["greetings", "yes", "afirmative", "dance1", "dance2", "follow"]
        self.move_list = [self.greetings_movment, self.yes_head, self.yes_head, self.dance_1, self.dance_2, self.folow_movment]

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
        self.initialize_position(True)
        

    def run(self):
        text = "";
        while True:
            text = self.movment_pipe.recv()
            
            if text in self.move_list_words:
                try:
                    self.move_list[self.move_list_words.index(text)]()
                except Exception as e:
                    print(e)
                    self.reset_position()
            elif text == "exit":
                break
            else:
                continue


    def initialize_position(self, initialPos=False):
            
            self.rshoulder.angle = 1
            self.relbow.angle = 90
            self.rarm.angle = 5

            self.lshoulder.angle = 1
            self.lelbow.angle = 90
            self.larm.angle = 180

            self.hyaw.angle = 90
            self.hroll.angle = 92
            self.hpitch.angle = 90

            if initialPos:
                return

            asyncio.run(self.move_servo(self.rshoulder, 175, 0.4))
            asyncio.run(self.move_servo(self.relbow, 175, 0.4))
            asyncio.run(self.move_servo(self.rarm, 1, 0.2))

            asyncio.run(self.move_servo(self.lshoulder, 180, 0.4))
            asyncio.run(self.move_servo(self.lelbow, 0, 0.4))
            asyncio.run(self.move_servo(self.larm, 177, 0.2))

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
            asyncio.run(self.move_servo(self.hpitch, 90, 0.2))
            asyncio.run(self.move_servo(self.hyaw, 90, 0.2))
            # move the hands to the init position
            # first elbow
            asyncio.run(self.move_servo(self.relbow, 90, 0.4))
            asyncio.run(self.move_servo(self.lelbow, 90, 0.4))
            # then shoulder
            asyncio.run(self.move_servo(self.rshoulder, 1, 0.4))
            asyncio.run(self.move_servo(self.lshoulder, 0, 0.4))
            # then arm
            asyncio.run(self.move_servo(self.rarm, 1, 0.2))
            asyncio.run(self.move_servo(self.larm, 180, 0.2))


    def reset_position(self):
        # move the head
        asyncio.run(self.move_servo(self.hroll, 92, 0.4))
        asyncio.run(self.move_servo(self.hpitch, 90, 0.2))
        asyncio.run(self.move_servo(self.hyaw, 90, 0.2))
        # move the hands to the init position
        # first elbow
        asyncio.run(self.move_servo(self.relbow, 90, 0.4))
        asyncio.run(self.move_servo(self.lelbow, 90, 0.4))
        # then shoulder
        asyncio.run(self.move_servo(self.rshoulder, 1, 0.4))
        asyncio.run(self.move_servo(self.lshoulder, 1, 0.4))
        # then arm
        asyncio.run(self.move_servo(self.rarm, 1, 0.2))
        asyncio.run(self.move_servo(self.larm, 180, 0.2))



    # arm movments

    def greetings_movment(self):
            asyncio.run(self.move_servo(self.rshoulder, 175, 0.5))
            asyncio.run(self.move_servo(self.relbow, 90, 0.5))
            asyncio.run(self.move_servo(self.rarm, 1, 0.3))

            # move the elbow in swing)
            asyncio.run(self.swing_servo(self.relbow, 65, 105, 5,0.2))

            asyncio.run(self.move_servo(self.rarm, 1, 0.3))
            asyncio.run(self.move_servo(self.relbow, 92, 0.5))
            asyncio.run(self.move_servo(self.rshoulder, 1, 0.5))


    

    # head movments
    def yes_head(self):
            asyncio.run(self.swing_servo(self.hpitch, 65, 105, 5,0.2))
            asyncio.run(self.move_servo(self.hpitch, 90, 0.5))



    # dance movments
    def dance_1(self):
        asyncio.run(self.move_servo(self.relbow, 95, 0.5))
        asyncio.run(self.move_servo(self.lelbow, 85, 0.5))
        asyncio.run(self.move_servo(self.rarm, 90, 0.5))
        asyncio.run(self.move_servo(self.larm, 100, 0.5))

        for i in range(0,4):
            asyncio.run(self.move_servo(self.rshoulder, 90, 0.2))
            asyncio.run(self.move_servo(self.lshoulder, 90, 0.2))
            asyncio.run(self.move_servo(self.rshoulder, 1, 0.2))
            asyncio.run(self.move_servo(self.lshoulder, 1, 0.2))

        self.reset_position()
    


    def dance_2(self):
        asyncio.run(self.move_servo(self.rshoulder, 90, 0.2))
        asyncio.run(self.move_servo(self.lshoulder, 90, 0.2))

        for i in range(0,2):
            asyncio.run(self.move_servo(self.rarm, 90, 0.1))
            asyncio.run(self.move_servo(self.larm, 100, 0.1))
            asyncio.run(self.move_servo(self.rarm, 1, 0.1))
            asyncio.run(self.move_servo(self.larm, 180, 0.1))
        
        asyncio.run(self.move_servo(self.rshoulder, 120, 0.2))
        asyncio.run(self.move_servo(self.lshoulder, 177, 0.2))
        
        for i in range(0,3):
            asyncio.run(self.move_servo(self.rshoulder, 120, 0.2))
            asyncio.run(self.move_servo(self.relbow, 30, 0.2))

            asyncio.run( self.concat_movments([self.move_servo(self.hyaw, 160, 2.5), self.move_servo(self.relbow, 150, 2.5)]))
            asyncio.run(self.move_servo(self.relbow, 90, 0.1))
            asyncio.run(self.move_servo(self.rshoulder, 177, 0.2))

            asyncio.run(self.move_servo(self.lshoulder, 120, 0.2))
            asyncio.run(self.move_servo(self.lelbow, 150, 0.2))

            asyncio.run(self.concat_movments([self.move_servo(self.hyaw, 10, 2.5), self.move_servo(self.lelbow, 30, 2.5)]))
            asyncio.run(self.move_servo(self.lelbow, 90, 0.1))
            asyncio.run(self.move_servo(self.lshoulder, 177, 0.2))
        
        self.reset_position()




            
    #---------------------------------------------------------------------------------------------------
    # *                                      MQTT FUNCTIONS                                             *
    # ?  Simulate movments sent by the app via mqtt
    #---------------------------------------------------------------------------------------------------
        
    # folow movments
    def folow_movment(self):

        print('Connecting MQTT')
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message_movment
        client.connect(self.env_vars['MQTT_HOST'], int(self.env_vars['MQTT_PORT']), 60)

        print("Starting movment")
        # start the loop
        while True:
            # check if text is aviable in pipe  

            if self.movment_pipe.poll():
                text = self.movment_pipe.recv()
                if text == 'stop':
                    break
            else:
                client.loop()

        client.disconnect()
        client.loop_stop()
        self.reset_position()

    #---------------------------
    # *   Auxiliar functions mqtt 
    #---------------------------

    # on connect
    def on_connect(self, client, userdata, flags, rc):
        topic_suscribe = self.env_vars['MQTT_TOPIC_MOVMENT']
        client.subscribe(topic_suscribe)
        

    # on message
    def on_message_movment(self, client, userdata, msg):
        movment = msg.payload.decode()

        data = json.loads(movment)


        if(time.time() - self.last_movment < 0.5):
            return
        
        self.last_movment = time.time()

        data['rshoulder'] = self.map_value(data['rshoulder'], self.env_vars['R_SHOULDER_MOVMENT_MIN'], self.env_vars['R_SHOULDER_MOVMENT_MAX'], 90, self.env_vars['R_ELBOW_MAX'])
        data['relbow'] = self.map_value(data['relbow'], self.env_vars['R_ELBOW_MOVMENT_MIN'], self.env_vars['R_ELBOW_MOVMENT_MAX'], self.env_vars['R_ARM_MIN'], self.env_vars['R_ARM_MAX'])
        data['lshoulder'] = self.map_value(data['lshoulder'], self.env_vars['L_SHOULDER_MOVMENT_MIN'], self.env_vars['L_SHOULDER_MOVMENT_MAX'], 100, self.env_vars['L_ELBOW_MAX'])
        data['lrelbow'] = self.map_value(data['lrelbow'], self.env_vars['L_ELBOW_MOVMENT_MIN'], self.env_vars['L_ELBOW_MOVMENT_MAX'], self.env_vars['L_ARM_MIN'], self.env_vars['L_ARM_MAX'])

        # preaty print
        print('Movment: ', data)



        # move the robot
        function_list=[
            self.move_servo(self.relbow, data['rshoulder'], 0.2),
            self.move_servo(self.rarm, data['relbow'], 0.2),
            self.move_servo(self.lelbow, data['lshoulder'], 0.2),
            self.move_servo(self.larm, data['lrelbow'], 0.2)
        ]
        asyncio.run(self.concat_movments(function_list))

        




    #---------------------------
    # *   General propouse functions
    #---------------------------
    
    # function to map a value from one range to another and if is out of range return the min or max value
    def map_value(self, value, in_min, in_max, out_min, out_max, inverted=False):
        # convet values to int
        
        value = int(value)
        in_min = int(in_min)
        in_max = int(in_max)
        out_min = int(out_min)
        out_max = int(out_max)
        if inverted:
            value = in_max - value

        if value < in_min:
            return out_min
        elif value > in_max:
            return out_max
        else:
            return int(np.interp(value, [in_min, in_max], [out_min, out_max]))
        



    #---------------------------------------------------------------------------
    # *                           Auxiliar functions async for movment         *
    # ?  Moves the robot async
    #---------------------------------------------------------------------------

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

    async def concat_movments(self, function_list):
        await asyncio.gather(*function_list)




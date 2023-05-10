#!/usr/bin/env python3
import asyncio
import sys
import multiprocessing as mp
import time
import os
import signal


# modules
import modules.tts as tts
import modules.chat as chat
import modules.camera as camera
import modules.movment as mv

# this program is a bot with 9 servo motors; 3 on the head for turn left, right, and up/down 
# and 6 on the arms: one from shoulder to elbow, one from elbow to wrist, and one from wrist to hand
# the bot will be able to move its head and arms, speak and voice recognition

class Robot():
    def __init__(self):
        # initialize pipes
        self.tts_pipe = mp.Pipe()
        self.vr_pipe = mp.Pipe()
        self.movment_pipe = mp.Pipe()
        self.ring_led_pipe = mp.Pipe()
        self.camera_pipe = mp.Pipe()
        self.chat_pipe = mp.Pipe()

        self.camera_commands=["foto", "face", "video"]

        self.initialize()

    


    def initialize(self):
        # initialize modules
        self.tts = tts.TTS(self.tts_pipe[1])
        self.chat = chat.Chat(self.chat_pipe[1])
        self.mv = mv.Movment(self.movment_pipe[1])
        # self.camera = camera.Camera(self.camera_pipe[1])
        #self.vr = modules.vr.VoiceRecognition(self.vr_pipe)
        #self.servo = modules.servo.Servo(self.servo_pipe)
        #self.ring_led = modules.ring_led.RingLed(self.ring_led_pipe)

        # start modules
        self.tts.start()
        self.chat.start()
        self.mv.start()
        # self.camera.start()
        #self.vr.start()
        #self.ring_led.start()

        # modify pipes to be senders
        self.tts_pipe = self.tts_pipe[0]
        self.chat_pipe = self.chat_pipe[0]
        self.movment_pipe = self.movment_pipe[0]
        # self.camera_pipe = self.camera_pipe[0]
        #self.vr_pipe = self.vr_pipe[0]
        #self.ring_led_pipe = self.ring_led_pipe[0]


    def run(self):
        self.tts_pipe.send("Hola soy un robot!")
        while True:
            # get input from keyboard
            text = input("Que quieres que te ayude?: ")
            if text == "exit":
                break
            if text == "hi":
                self.movment_pipe.send("greetings")
                continue


            # elif text in self.camera_commands:
            #     self.camera_pipe.send(text)
            #     res =self.camera_pipe.recv()
            #     if res == True:
            #         print("Foto tomada")
            #     else:
            #         print("No se pudo tomar la foto " + res)
            #     continue
                
            # elif text == "":
            #     continue

            self.chat_pipe.send(text)
            response = self.chat_pipe.recv()
            print(response)
            self.tts_pipe.send(response)


    
    def stop(self):
        self.tts_pipe.send("Adios!")
        self.tts_pipe.send("exit")
        self.chat_pipe.send("exit")
        self.camera_pipe.send("exit")
        #self.vr_pipe.send("exit")
        #self.servo_pipe.send("exit")
        #self.ring_led_pipe.send("exit")

        time.sleep(1)
        self.tts.terminate()
        self.chat.terminate()
        self.camera.terminate()
        #self.vr.terminate()
        #self.servo.terminate()
        #self.ring_led.terminate()


# main 
if __name__ == '__main__':
    robot = Robot()
    try:
        robot.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except:
        print("Unexpected error:", sys.exc_info()[0])
    # print in red exiting
    print("\033[91mExiting\033[0m")
    time.sleep(1)
    robot.stop()
    sys.exit(0)


#!/usr/bin/env python3
import asyncio
import sys
import multiprocessing as mp
import time
import os
import signal
import json
from dotenv import dotenv_values


# modules
import modules.tts as tts
import modules.chat as chat
import modules.camera as camera
import modules.movment as mv
import modules.screen as screen
# import modules.mqtt as mqtt



class Robot():
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UDERLINE = '\033[4m'

    def __init__(self, env_vars):
        # initialize pipes
        self.tts_pipe = mp.Pipe()
        self.chat_pipe = mp.Pipe()
        self.movment_pipe = mp.Pipe()
        self.screen_pipe = mp.Pipe()
        self.vr_pipe = mp.Pipe()
        self.ring_led_pipe = mp.Pipe()
        self.camera_pipe = mp.Pipe()
        self.mqtt_pipe = mp.Pipe()

        self.camera_commands=["foto", "face", "video"]

        self.env_vars = env_vars

        self.initialize()

    


    def initialize(self):
        # initialize modules
        self.tts = tts.TTS(self.tts_pipe[1])
        self.chat = chat.Chat(self.chat_pipe[1], self.env_vars.get('OPENAI_TOKEN'))
        self.mv = mv.Movment(self.movment_pipe[1], self.env_vars)
        print("Starting screen")
        # self.screen = screen.Screen(self.screen_pipe[1])
        # self.camera = camera.Camera(self.camera_pipe[1])
        #self.vr = modules.vr.VoiceRecognition(self.vr_pipe)
        #self.servo = modules.servo.Servo(self.servo_pipe)
        #self.ring_led = modules.ring_led.RingLed(self.ring_led_pipe)
        #self.mqtt = modules.mqtt.Mqtt(self.mqtt_pipe, func)


        print("AAA")

        # start modules
        self.tts.start()
        self.chat.start()
        self.mv.start()
        # self.screen.start()
        # self.camera.start()
        #self.vr.start()
        #self.ring_led.start()
        #self.mqtt.start()

        # modify pipes to be senders
        self.tts_pipe = self.tts_pipe[0]
        self.chat_pipe = self.chat_pipe[0]
        self.movment_pipe = self.movment_pipe[0]
        # self.screen_pipe = self.screen_pipe[0]
        # self.camera_pipe = self.camera_pipe[0]
        #self.vr_pipe = self.vr_pipe[0]
        #self.ring_led_pipe = self.ring_led_pipe[0]
        #self.mqtt_pipe = self.mqtt_pipe[0]


    def run(self):
        self.tts_pipe.send("Hola soy un robot!")
        while True:
            # get input from keyboard
            text = input(self.bcolors.ENDC+"\nQue quieres que te ayude?: "+self.bcolors.OKCYAN)
            if text == "exit" or text=="q":
                break
            if text == "hi":
                self.movment_pipe.send("greetings")
                continue
            elif text=="yes" or text=="afirmative":
                self.movment_pipe.send("yes")
                continue   
            elif text=="dance1" or text=="dance2" or text=="dance3":
                self.movment_pipe.send(text)
                continue
            elif text=="follow":
                self.movment_pipe.send("follow")
                input(self.bcolors.FAIL + " Pulsa enter para parar... " + self.bcolors.ENDC)
                self.movment_pipe.send("stop")
                continue
            else:
                self.chat_pipe.send(text)
                response = self.chat_pipe.recv()
                print(self.bcolors.OKGREEN + response["message"] + self.bcolors.ENDC)
                self.tts_pipe.send(response["message"])


    
    def stop(self):
        self.tts_pipe.send("Adios!")
        self.tts_pipe.send("exit")
        self.chat_pipe.send("exit")
        self.movment_pipe.send("exit")
        # self.screen_pipe.send("exit")


        time.sleep(1)
        self.tts.terminate()
        self.chat.terminate()
        self.mv.terminate()
        # self.screen.terminate()

# main 
if __name__ == '__main__':
    robot = Robot(dotenv_values('.env'))
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


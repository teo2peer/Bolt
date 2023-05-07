
import multiprocessing as mp
import time
import random
import subprocess
import math

from datetime import datetime
import os, sys

import board
import neopixel



class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class RingLed(mp.Process):

    def __init__(self, ring_led_pipe):
        super().__init__()
        # init pipe message queue
        self.ring_led_pipe = ring_led_pipe

        # init the neopixel ring
        self.ring = neopixel.NeoPixel(board.D18, 8, brightness=0.2, auto_write=False)



        self.ring.fill((0, 0, 0))
        self.ring.show()
        time.sleep(0.1)
        


        self.animation=self.animation(self.ring)
        
    def run(self):
        pass
        




    def true_pos(self, pos):
        print("Changing: " + bcolors.OKGREEN + str(pos) + bcolors.ENDC+" to ",end=" ")
        if pos<=3:
            pos = pos + 3 if pos+3<8 else pos+3-8
        elif pos>3:
            pos = pos+3 if (pos+3<8)else pos+4-9
        print(bcolors.FAIL + str(pos) + bcolors.ENDC)
        return abs(pos%8)

    def clear(self):
        for i in range(8):
            self.ring[self.true_pos(i)] = (0, 0, 0)
            self.ring.show()
            time.sleep(0.1)

    def wipe(self, color):
        for i in range(8):
            self.ring[self.true_pos(i)] = color
            self.ring.show()
            time.sleep(0.1)
    
    def wipe_erase(self, color):
        for i in range(8):
            self.ring[self.true_pos(i)] = (0, 0, 0)
            self.ring.show()
            time.sleep(0.1)
        self.clear()
        
    class animation:

        def __init__(self, ring):
            self.ring = ring
            self.processes = []

        def true_pos(self, pos):
            # print("Changing: " + bcolors.OKGREEN + str(pos) + bcolors.ENDC,end=" ")

            if pos<=3 and pos>=0:
                pos = pos + 3 if pos+3<8 else pos+3-8
                # print(" to "+bcolors.FAIL + str(pos) + bcolors.ENDC)
            elif pos>3 and pos<=7:
                pos = pos+3 if (pos+3<8)else pos+4-9
                # print(" to "+bcolors.FAIL + str(pos) + bcolors.ENDC)
            elif pos>7:
                pos = pos%8
                # print(" to an little number "+bcolors.FAIL + str(pos) + bcolors.ENDC)
                pos = pos + 3 if pos+3<8 else pos+3-8
            elif pos <0:
                pos = 8+(pos)
                # print("sign to "+bcolors.WARNING + str(pos) + bcolors.ENDC, end=" ")
                pos = pos+3 if (pos+3<8)else pos+4-9
                # print(" with real pos "+bcolors.FAIL + str(pos) + bcolors.ENDC)
            return abs(pos%8)

        def clear(self):
            for i in range(8):
                self.ring[self.true_pos(i)] = (0, 0, 0)
                self.ring.show()
                time.sleep(0.1)

        def full_direction(self, array, color, delay):
            """
            Direction full and after wipe
            :param array:
            :param color:
            :param delay:
            """
            for i in range(5):
                for j in range(2):
                    if (array[i][j] != 9):    
                        self.ring[self.true_pos(array[i][j])] = color
                self.ring.show()
                time.sleep(delay)
                
            if(color!=(0,0,0)):
                self.full_direction(array,(0,0,0),delay)

        def full_direction_single(self, array, color, delay):
            """
            Direction 1 by 1
            :param array:
            :param color:
            :param delay:
            """
            for i in range(5):
                for j in range(2):
                    
                    if (array[i][j] != 9):    
                        self.ring[self.true_pos(array[i][j])] = color
                    if(i!=0 and i != len(array)):
                        self.ring[self.true_pos(array[i-1][j])] = (0,0,0)
                self.ring.show()
                time.sleep(delay)

            for i in range(2):
                self.ring[self.true_pos(array[len(array)-1][i])] = (0,0,0)
                self.ring[self.true_pos(array[len(array)-2][i])] = (0,0,0)

            self.ring.show()
            time.sleep(delay)
                




        def l_to_r(self, color, delay=0.1):
            order_led = [[6,9], [7,5],[4,0],[1,3],[2,9]]
            self.full_direction(order_led, color, delay)
            

        def r_to_l(self, color, delay=0.1):
            order_led = [[6,9], [7,5],[4,0],[1,3],[2,9]]
            order_led.reverse()
            self.full_direction(order_led, color, delay)

        def u_to_d(self, color, delay=0.1):
            order_led = [[0,9],[1,7],[2,6],[3,5],[4,9]]
            self.full_direction(order_led, color, delay)

        def d_to_u(self, color, delay=0.1):
            order_led = [[0,9],[1,7],[2,6],[3,5],[4,9]]
            order_led.reverse()
            self.full_direction(order_led, color, delay)


        # just 1 row at tim
        def l_to_rs(self, color, delay=0.1):
            order_led = [[6,9], [7,5],[4,0],[1,3],[2,9]]
            self.full_direction_single(order_led, color, delay)

        def r_to_ls(self, color, delay=0.1):
            order_led = [[6,9], [7,5],[4,0],[1,3],[2,9]]
            order_led.reverse()
            self.full_direction_single(order_led, color, delay)


        def u_to_ds(self, color, delay=0.1):
            order_led = [[0,9],[1,7],[2,6],[3,5],[4,9]]
            self.full_direction_single(order_led, color, delay)

        def d_to_us(self, color, delay=0.1):
            order_led = [[0,9],[1,7],[2,6],[3,5],[4,9]]
            order_led.reverse()
            self.full_direction_single(order_led, color, delay)

        def start(self, function, color, tail=1, delay=0.1):
            # start loading with multiprocessing that can be stopped later
            if(function == "loading"):
                self.processes.append(Process(target=self.loading, args=(color, tail, delay)))
                self.processes[-1].start()
                print(bcolors.OKGREEN + "#############\nLoading animation started\n#############" + bcolors.ENDC)

        
        def stop(self):
            for process in self.processes:
                process.terminate()
            self.processes = []
            self.clear()
            print(bcolors.OKGREEN + "#############\nAll animation stopped\n#############" + bcolors.ENDC)

        def loading(self, color, tail=1, delay=0.1):
            while True:
                # detect multiprocessing join
                for i in range(8):
                    self.ring[self.true_pos(i)] = color
                    self.ring[self.true_pos(i-tail-1)] = (0,0,0)
                    
                    self.ring.show()
                    time.sleep(delay)

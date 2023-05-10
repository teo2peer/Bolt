# use the PCA9685 library
import time   
from adafruit_servokit import ServoKit
import multiprocessing as mp
import numpy as np



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
        self.hpitch = self.pca.servo[9]
        self.hroll = self.pca.servo[10]

    def run(self):
        text = "";
        while True:
            text = self.movment_pipe.recv()
            
            if text == "greetings":
                self.greetingsMovment()
            
            if text != "":
                continue
            elif text == "exit":
                break
            else:
                continue

    def greetingsMovment(self):
        # greetings with the right arm
        self.rshoulder.angle = 180
        self.relbow.angle = 90
        self.rarm.angle = 90

        self.move_arm(0, 90, 1)

    



    def move_arm(self, theta1, theta2, theta3):
        # Dimensiones de los eslabones del brazo
        L1 = 5
        L2 = 7
        L3 = 3

        # Matrices de transformación de Denavit-Hartenberg
        T01 = np.array([[np.cos(theta1), -np.sin(theta1), 0, 0],
                        [np.sin(theta1), np.cos(theta1), 0, 0],
                        [0, 0, 1, L1],
                        [0, 0, 0, 1]])

        T12 = np.array([[np.cos(theta2), -np.sin(theta2), 0, L2],
                        [0, 0, -1, 0],
                        [np.sin(theta2), np.cos(theta2), 0, 0],
                        [0, 0, 0, 1]])

        T23 = np.array([[np.cos(theta3), -np.sin(theta3), 0, L3],
                        [np.sin(theta3), np.cos(theta3), 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])

        # Matriz de transformación total
        T03 = T01 @ T12 @ T23

        # Coordenadas del efector final
        x = T03[0, 3]
        y = T03[1, 3]
        z = T03[2, 3]

        # Cálculo de los ángulos de los servos
        a1 = np.arctan2(y, x)
        a2 = np.arctan2(z - L1, np.sqrt(x**2 + y**2))
        a3 = np.arctan2(np.sin(theta3) * np.sqrt(x**2 + y**2), np.cos(theta3) * np.sqrt(x**2 + y**2) + L3)

        # Conversión de ángulos a pulsos
        pulse1 = int(self.MIN_IMP[0] + (self.MAX_IMP[0] - self.MIN_IMP[0]) * (a1 - self.MIN_ANG[0]) / (self.MAX_ANG[0] - self.MIN_ANG[0]))
        pulse2 = int(self.MIN_IMP[1] + (self.MAX_IMP[1] - self.MIN_IMP[1]) * (a2 - self.MIN_ANG[1]) / (self.MAX_ANG[1] - self.MIN_ANG[1]))
        pulse3 = int(self.MIN_IMP[2] + (self.MAX_IMP[2] - self.MIN_IMP[2]) * (a3 - self.MIN_ANG[2]) / (self.MAX_ANG[2] - self.MIN_ANG[2]))

        # Movimiento suave de los servos a las posiciones deseadas
        self.move_servo_smoothly(self.rshoulder, pulse1)
        self.move_servo_smoothly(self.relbow, pulse2)
        self.move_servo_smoothly(self.rarm, pulse3)

    def move_servo_smoothly(self, servo, pulse):
        # Obtiene el pulso actual del servo
        current_pulse = servo.pulse_width

        # Si el pulso actual es mayor al pulso deseado, se disminuye el pulso actual hasta llegar al pulso deseado
        if current_pulse > pulse:
            while current_pulse > pulse:
                current_pulse -= 1
                servo  = current_pulse
                time.sleep(0.01)

        # Si el pulso actual es menor al pulso deseado, se aumenta el pulso actual hasta llegar al pulso deseado
        elif current_pulse < pulse:
            while current_pulse < pulse:
                current_pulse += 1
                servo = current_pulse
                time.sleep(0.01)

        # Si el pulso actual es igual al pulso deseado, no se hace nada
        else:
            pass

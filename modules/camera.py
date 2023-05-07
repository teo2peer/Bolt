import multiprocessing as mp
import cv2
import sys
import time

class Camera(mp.Process):
    def __init__(self, camera_pipe):
        super().__init__()
        self.cam_pipe = camera_pipe
        
        try:
            self.cam = cv2.VideoCapture(0)
            if not self.cam.isOpened():
                raise Exception('Camera not found')
        except:
            self.cam = cv2.VideoCapture(1)
            if not self.cam.isOpened():
                sys.exit()

        


        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cam.set(cv2.CAP_PROP_FPS, 3)
        
        
        # face detection
        self.face_cascade = cv2.CascadeClassifier('/home/pi/robot/modules/data/haarcascades/haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier('/home/pi/robot/modules/data/haarcascades/haarcascade_eye.xml')

    def run(self):
        # await for camera_pipe asking for thing
        while True:
            try:
                text = self.cam_pipe.recv()
                if text == "foto":
                    # capture frame and save it in tmp/images/foto.png
                    self.cam_pipe.send(self.capture_photo())
                elif text == "face":
                    self.cam_pipe.send(self.capture_face())
                elif text == "exit":
                    self.cam.release()
                    break
                else:
                    self.cam_pipe.send(False)
            except:
                self.cam_pipe.send(False)
            
    
    def capture_photo(self):
        try:
            ret, frame = self.cam.read()
            cv2.imwrite('/home/pi/robot/tmp/images/foto.png', frame)

            return True
        except Exception as e:
            return e
    
    def capture_face(self):
        # capture frame and save it in tmp/images/face.png
        try:
            ret, frame = self.cam.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x,y,w,h) in faces:
                cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                for (ex,ey,ew,eh) in eyes:
                    cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
            cv2.imwrite('/home/pi/robot/tmp/images/face.png', frame)

            return True
        except:
            return False

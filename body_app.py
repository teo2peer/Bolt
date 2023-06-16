import cv2
import mediapipe as mp
import math
import time
import paho.mqtt.client as mqtt
import json
import threading
import queue


broker = "192.168.0.49"  # Dirección del broker MQTT
port = 1883  # Puerto del broker MQTT
topic = "robot_pose"  # Tema al que se enviarán los datos
message_queue = queue.Queue()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conexión exitosa al broker MQTT")
    else:
        print(f"No se pudo conectar al broker. Código de resultado: {rc}")



def calculate_angle(a, b, c):
    # Calcula el ángulo entre tres puntos utilizando el teorema del coseno
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle


def send_data(client):
    start_time = time.time()  # Obtener el tiempo de inicio
    global rshoulder_angle, relbow_angle, lshoulder_angle, lrelbow_angle
    while True:
        message = message_queue.get()
        message_queue.task_done()
        if message == "stop":
            break
        rshoulder_angle, relbow_angle, lshoulder_angle, lrelbow_angle = message

        current_time = time.time()  # Obtener el tiempo actual

        if current_time - start_time >= 0.5:
            # empaquetar los datos en un json
            data = {
                "rshoulder": rshoulder_angle,
                "relbow": relbow_angle,
                "lshoulder": lshoulder_angle,
                "lrelbow": lrelbow_angle
            }

            # Enviar el dato cada 0.5 segundos
            client.publish(topic, json.dumps(data))

            start_time = current_time  # Reiniciar el tiempo de inicio

        client.loop()  # Mantener la conexión MQTT activa

def main():
    start_time = time.time()  # Obtener el tiempo de inicio

    
    print("Iniciando cámara y MediaPipe")
    cap = cv2.VideoCapture(0)  # Abrir la cámara predeterminada

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    print("Poses y camera inicializada")

    print("Iniciando conexión MQTT")
    client = mqtt.Client()  # Crear instancia del cliente MQTT
    client.on_connect = on_connect  # Configurar función de conexión

    client.connect(broker, port)  # Conectar al broker MQTT

    print("Conectado al broker MQTT")

    print("Iniciando thread de envío de datos")
    thread = threading.Thread(target=send_data, args=(client,))
    thread.start()



    while True:
        ret, frame = cap.read()

        # Convertir la imagen a RGB para el procesamiento de MediaPipe
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # mirror the image
        image = cv2.flip(image, 1)

        image.flags.writeable = False

        # Realizar el seguimiento de la pose
        results = pose.process(image)

        # Convertir la imagen nuevamente a BGR para la visualización
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        

        # Dibujar el esqueleto en la imagen y calcular los ángulos
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Obtener las coordenadas de los puntos de interés
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            neck = [landmarks[mp_pose.PoseLandmark.NOSE].x,
                    landmarks[mp_pose.PoseLandmark.NOSE].y]

            # Calcular los ángulos del hombro y el codo
            relbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            lelbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
            
            rshoulder_angle = calculate_angle(left_elbow, neck, right_shoulder)
            lshoulder_angle =calculate_angle(right_elbow, neck, left_shoulder)


            # Mostrar los ángulos en pantalla
            cv2.putText(image, f'Codo Izquierda: {round(lelbow_angle, 2)}  Derecha: {round(relbow_angle, 2)} degrees',
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(image, f'Hombro Izquierda: {round(lshoulder_angle, 2)}  Derecha: {round(rshoulder_angle, 2)} degrees',
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Dibujar el esqueleto
            mp.solutions.drawing_utils.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # Agregar los ángulos a la cola de mensajes
            current_time = time.time()  # Obtener el tiempo actual

            if current_time - start_time >= 0.5:
                message_queue.put((rshoulder_angle, relbow_angle, lshoulder_angle, lelbow_angle))
                start_time = current_time  # Reiniciar el tiempo de inicio
            

            # Enviar los datos por MQTT
        # Mostrar la imagen resultante
        cv2.imshow('Pose Estimation', image)

        # Presionar 'q' para salir del bucle
        if cv2.waitKey(1) & 0xFF == ord('q'):
            client.disconnect()  # Desconectar del broker MQTT
            client= None
            message_queue.put("stop")
            break

    cap.release()
    cv2.destroyAllWindows()
    thread.join()

if __name__ == '__main__':
    main()

import paho.mqtt.client as mqtt
import json

class MQTT(mp.Process):
    def __init__(self, mqtt_pipe, function_to_execute, lang="es"):
        super().__init__()
        self.mqtt_pipe = mqtt_pipe

        # MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect("localhost", 1883, 60)

        self.function_to_execute = function_to_execute





    def run(self):
        # Loop to receive text from the main process
        # if the text is not empty, it will generate the TTS
        # if new text is received, it will overwrite the previous TTS
        text = "";
        while True:
            text = self.chat_pipe.recv()
            if text != "":
                message = self.get_prompt(text)
                self.chat_pipe.send(message)
                text = ""
            elif text == "exit":
                break
            else:
                continue
    


    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

    def on_message(self, client, userdata, msg):
        self.function_to_execute(msg.payload.decode())

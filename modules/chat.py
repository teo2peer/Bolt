
import multiprocessing as mp
import requests as rq
import openai
import json

class Chat(mp.Process):
    def __init__(self, chat_pipe, lang="es"):
        super().__init__()
        self.chat_pipe = chat_pipe

        self.openaiToken = "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"
        self.messages = [
           {"role": "system", "content": "Eres un asistente virtual con gracia y personalidad divertida y ironica a veces, que ayuda a las personas dandoles la informacion necesaria. "},
            {"role": "system", "content": "Tus respuestas deben ser graciosas pero dando la informacion necesaria y no deben ser respuestas de mas de 150 palabras. A veces puedes burlarte de los usuarios " },
            {"role": "system", "content": "Devolveras toda la respuesta en formato json donde contendra el estado de aninmo (feliz, triste, ironico, animado, enfadado...) que te ha producid, ejemplo de tu respuesta: {\"mood\":\"feliz\",\"message\":\"este es el mensaje\"} " },
            {"role": "assistant", "content":"{\"mood\":\"feliz\",\"message\":\"vale, de acuerdo, ya vere yo lo que haga, chaval\"}"},
        ]
        openai.api_key = self.openaiToken




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
    


    def get_prompt(self, text):
        self.messages.append({"role": "user", "content": text})
        self.completion = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = self.messages,
            temperature = 0.5
        )
        response = self.completion["choices"][0]["message"].content
        response.replace("\'","\"")
        self.messages.append({"role": "assistant", "content": response})
        # if len(self.messages) > 9 remove the 4rd and 5th message
        if len(self.messages) > 8:
            self.messages.pop(4)
            self.messages.pop(4)
        
        return json.loads(response)

from openai import OpenAI
import os
import cv2
import yt_dlp
import base64
from queue import Queue
import time
import json
import dashscope
from dashscope.audio.tts import SpeechSynthesizer
import pygame
import io

API_KEY = "YOUR_API_KEY"
dashscope.api_key = API_KEY
video_path = 'YOUR YOUTUBE LINK' # https://www.youtube.com/watch?v=1MLCFqyEJsA

class Dass:

    def __init__(self, tts_model="sambert-zhichu-v1", voice='longxiaochun'):
        self.client = self._get_client()
        self.memory = Queue(6)
        self.tts_client = self._get_tts_client(tts_model, voice)

    def _get_client(self):
        client = OpenAI(
            api_key=API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        return client

    def _get_tts_client(self, tts_model, voice):
        return tts_model
    
    def voice(self, text):
        print(self.tts_client)
        result = SpeechSynthesizer.call(model=self.tts_client,
                                text=text,
                                sample_rate=48000,
                                format='wav')
        
        self._play(result.get_audio_data())

    def _play(self, audio):
        pygame.mixer.init()
        audio_stream = io.BytesIO(audio)
        pygame.mixer.music.load(audio_stream)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    def apply_chat(self, base64img, format='png'):
        formwork = f"data:image/{format};base64,{base64img}"
        return formwork


    def encode64(self, png):
        with open(png, 'rb') as f:
            img = f.read()
            return str(base64.b64encode(img), 'utf-8')
        
    def response(self, img, format):
        base64img = self.encode64(img)
        new_img_url = self.apply_chat(base64img=base64img, format=format)
        if self.memory.full() == True:
            self.memory.get()
        self.memory.put(new_img_url)
        if self.memory.qsize() >= 4:
            video = list(self.memory.queue)
            completion = self.client.chat.completions.create(
                model='qwen-vl-max-latest',
                messages=[
                    {
                        "role": "system",
                        "content": "你现在是一个陪我看视频的chatbot"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video",
                                "video": video
                            },
                            {
                                "type": "text",
                                "text": "根据画面内容随便聊聊，不要总是明显的问我问题，可以随意点。"
                            }
                        ] 
                    }
                ],
                temperature=1.8
            )

            response_json = json.loads(completion.model_dump_json())
            response = response_json['choices'][0]['message']['content']
            return response

        else:
            return "帧数只有4张"



def download_vedio(url, output_path="other.avi"):
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def extract_frames(video_path, dass:Dass, output="./img"):
    responses = []
    video_capture = cv2.VideoCapture(video_path)
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    pass_count = 0
    os.makedirs(output, exist_ok=True)

    print(f"Thread extrace_frames has get fps of {video_path}: {fps}")

    start_time = time.time()
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
            
        second = frame_count // int(fps)

        if frame_count % int(fps) == 0:
            print(f"{second}s of video passing...")
            img_name = os.path.join(output, f"frame_{second}.png")
            cv2.imwrite(img_name, frame)
            res = dass.response(img_name, format='png')
            if res != '帧数只有4张':
                print(res)
                dass.voice(res)
            with open("response.txt", 'a', encoding='utf-8') as fp:
                fp.write(res + "\n")
            responses.append(res)
            pass_count += 1

        frame_count += 1

        frames_name = sorted(os.listdir(output))
        exist_frames = len(frames_name)
        if exist_frames > 10:
            os.remove(os.path.join(output, frames_name[0]))
    video_capture.release()
    print(f"Totally passed piture is {pass_count}.")

download_vedio(video_path)
dass = Dass()
extract_frames("other.avi", dass)

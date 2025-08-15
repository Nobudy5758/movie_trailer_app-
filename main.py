import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from moviepy.editor import VideoFileClip, concatenate_videoclips
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")  # Environment se key load

class TrailerApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.add_widget(Label(text="Select a video file:", size_hint=(1, 0.1)))
        
        self.file_chooser = FileChooserListView(filters=['*.mp4'])
        self.add_widget(self.file_chooser)
        
        self.mode_spinner = Spinner(
            text='Select Mode',
            values=('Online', 'Offline'),
            size_hint=(1, 0.1)
        )
        self.add_widget(self.mode_spinner)
        
        self.generate_btn = Button(text="Generate Trailer", size_hint=(1, 0.1))
        self.generate_btn.bind(on_press=self.generate_trailer)
        self.add_widget(self.generate_btn)
        
        self.status_label = Label(text="", size_hint=(1, 0.1))
        self.add_widget(self.status_label)

    def generate_trailer(self, instance):
        if not self.file_chooser.selection:
            self.status_label.text = "No file selected!"
            return
        
        file_path = self.file_chooser.selection[0]
        mode = self.mode_spinner.text
        
        if mode == "Online":
            self.status_label.text = "Processing Online..."
            Clock.schedule_once(lambda dt: self.online_process(file_path), 0)
        elif mode == "Offline":
            self.status_label.text = "Processing Offline..."
            Clock.schedule_once(lambda dt: self.offline_process(file_path), 0)
        else:
            self.status_label.text = "Please select mode!"

    def online_process(self, file_path):
        try:
            API_URL = "https://api-inference.huggingface.co/models/your-model-id"
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

            with open(file_path, "rb") as f:
                response = requests.post(API_URL, headers=headers, data=f)

            if response.status_code != 200:
                self.status_label.text = f"API Error: {response.text}"
                return

            clip = VideoFileClip(file_path).subclip(0, 10)
            os.makedirs("trailers", exist_ok=True)
            output_path = os.path.join("trailers", "trailer_online.mp4")
            clip.write_videofile(output_path)

            self.status_label.text = f"Online trailer saved: {output_path}"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

    def offline_process(self, file_path):
        try:
            video_manager = VideoManager([file_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=30.0))
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()

            clips = []
            for start_time, end_time in scene_list[:3]:
                clip = VideoFileClip(file_path).subclip(start_time.get_seconds(), end_time.get_seconds())
                clips.append(clip)

            final_trailer = concatenate_videoclips(clips)
            os.makedirs("trailers", exist_ok=True)
            output_path = os.path.join("trailers", "trailer_offline.mp4")
            final_trailer.write_videofile(output_path)

            self.status_label.text = f"Offline trailer saved: {output_path}"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

class MyApp(App):
    def build(self):
        return TrailerApp()

if __name__ == "__main__":
    MyApp().run()

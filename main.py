import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import mainthread
from kivy.core.window import Window
import requests
import subprocess
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from moviepy.editor import VideoFileClip, concatenate_videoclips

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

class TrailerApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.selected_video = None

        self.label = Label(text="Select a video to create trailer", size_hint=(1, 0.1))
        self.add_widget(self.label)

        self.filechooser = FileChooserIconView(size_hint=(1, 0.6))
        self.filechooser.bind(on_selection=self.select_file)
        self.add_widget(self.filechooser)

        self.btn_online = Button(text="Generate Trailer (Online)", size_hint=(1, 0.15))
        self.btn_online.bind(on_press=lambda x: self.start_generation(online=True))
        self.add_widget(self.btn_online)

        self.btn_offline = Button(text="Generate Trailer (Offline)", size_hint=(1, 0.15))
        self.btn_offline.bind(on_press=lambda x: self.start_generation(online=False))
        self.add_widget(self.btn_offline)

    def select_file(self, chooser, selection):
        if selection:
            self.selected_video = selection[0]
            self.label.text = f"Selected: {os.path.basename(self.selected_video)}"

    def start_generation(self, online):
        if not self.selected_video:
            self.label.text = "Please select a video first!"
            return
        self.label.text = "Generating trailer..."
        threading.Thread(target=self.generate_trailer, args=(online,)).start()

    @mainthread
    def update_status(self, message):
        self.label.text = message

    def generate_trailer(self, online):
        try:
            if online:
                clips = self.detect_scenes_online()
            else:
                clips = self.detect_scenes_offline()

            if not clips:
                self.update_status("No scenes detected.")
                return

            final_clip = concatenate_videoclips(clips)
            output_path = os.path.join(os.path.dirname(self.selected_video), "trailer.mp4")
            final_clip.write_videofile(output_path)
            self.update_status(f"Trailer saved: {output_path}")

        except Exception as e:
            self.update_status(f"Error: {str(e)}")

    def detect_scenes_offline(self):
        video_manager = VideoManager([self.selected_video])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=30.0))
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scenes = scene_manager.get_scene_list()
        video_manager.release()

        clips = []
        for start, end in scenes[:5]:  # First 5 scenes
            clip = VideoFileClip(self.selected_video).subclip(start.get_seconds(), end.get_seconds())
            clips.append(clip)
        return clips

    def detect_scenes_online(self):
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        files = {"file": open(self.selected_video, "rb")}
        response = requests.post("https://api-inference.huggingface.co/models/your-model", headers=headers, files=files)

        # NOTE: Replace with your Hugging Face model processing
        scenes = [(0, 5), (10, 15), (20, 25)]  # Dummy data
        clips = []
        for start, end in scenes:
            clip = VideoFileClip(self.selected_video).subclip(start, end)
            clips.append(clip)
        return clips

class MovieTrailerApp(App):
    def build(self):
        Window.size = (400, 600)
        return TrailerApp()

if __name__ == "__main__":
    MovieTrailerApp().run()

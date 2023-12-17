# Existing imports...
import json
import os
import subprocess
import librosa
import soundfile as sf

from pydub import AudioSegment

from .dn_tracer import SentryEventLogger, DNSystemType, DNMsgStage, DNTag
from .file_uploader import FileUploader


# ResultsHandler class to handle the results
class ResultsHandler:
    def __init__(self, websocket, token):
        self.websocket = websocket
        self.token = token
        self.message_id = None
        self.errors = []
        self.files = []
        self.messages = []
        self.file_uploader = FileUploader()
        self.dn_tracer = SentryEventLogger(DNSystemType.DN_CLIENT.value)

        # Check if ffmpeg is installed
        self.ffmpeg_installed = self.check_ffmpeg()

        # Default target audio settings
        self.target_sample_rate = 41000
        self.target_bit_depth = 16
        self.target_channels = 2
        self.target_format = "wav"  # "wav", "mp3", "aiff", "flac", "ogg"

    def check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return True
        except FileNotFoundError:
            print("ffmpeg is not installed. Please install ffmpeg for audio processing.")
            return False

    def update_token(self, token):
        self.token = token

    def add_error(self, error):
        self.errors.append(error)

    def set_message_id(self, message_id):
        self.message_id = message_id

    async def add_file(self, file_path):
        # if not self.ffmpeg_installed:
        #     self.add_error("ffmpeg not installed, cannot process audio files.")
        #     return

        try:
            # Check and convert audio file if necessary
            converted_file_path = self.process_audio_file(file_path)
            file_url = await self.file_uploader.upload(converted_file_path, os.path.splitext(converted_file_path)[1][1:])
            self.files.append({'name': os.path.basename(converted_file_path), 'url': file_url})
        except Exception as e:
            self.dn_tracer.log_error(self.token, {
                DNTag.DNMsgStage.value: DNMsgStage.UPLOAD_ASSET.value,
                DNTag.DNMsg.value: str(e),
            })
            self.add_error(str(e))

    def process_audio_file(self, file_path):
        # Inspect audio file using librosa
        y, sr = librosa.load(file_path, sr=None)  # Load audio with original sample rate
        current_sample_rate = sr
        current_channels = 2 if len(y.shape) > 1 else 1  # Determine number of channels

        # Check if conversion is needed
        if (current_sample_rate != self.target_sample_rate or
                current_channels != self.target_channels):
            # Resample audio if needed
            if current_sample_rate != self.target_sample_rate:
                y = librosa.resample(y, current_sample_rate, self.target_sample_rate)

            # Write audio with target format and sample rate
            output_file_path = os.path.splitext(file_path)[0] + '.' + self.target_format
            sf.write(output_file_path, y.T if current_channels > 1 else y, self.target_sample_rate, format=self.target_format)

            # Adjust channels using pydub if needed
            if current_channels != self.target_channels:
                audio = AudioSegment.from_file(output_file_path)
                audio = audio.set_channels(self.target_channels)
                audio.export(output_file_path, format=self.target_format)

            return output_file_path
        else:
            return file_path


    async def add_message(self, message):
        self.messages.append(message)

    async def send(self):
        data = {
            "response": {
                "files": self.files,
                "error": ", ".join(self.errors) if self.errors else None,
                "message": ", ".join(self.messages) if self.messages else None,
                "status": 'completed',
            }
        }

        if self.message_id:
            data["response"]["id"] = self.message_id

        send_msg = {
            'token': self.token,
            'type': 'results',
            'data': data
        }

        await self.websocket.send(json.dumps(send_msg))

        self.dn_tracer.log_event(self.token, {
            DNTag.DNMsgStage.value: DNMsgStage.CLIENT_SEND_RESULTS_MSG.value,
            DNTag.DNMsg.value: json.dumps(send_msg),
        })
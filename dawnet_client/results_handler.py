# Existing imports...
import json
import os
import subprocess
import subprocess
from pydub import AudioSegment
from pydub.utils import mediainfo

from dawnet_client.file_uploader import FileUploader

from dawnet_client.dn_tracer import DNMsgStage, DNTag, SentryEventLogger, DNSystemType


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
        if not self.ffmpeg_installed:
            self.add_error("ffmpeg not installed, cannot process audio files.")
            return

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
        # Inspect audio file
        info = mediainfo(file_path)
        current_sample_rate = int(info['sample_rate'])
        current_bit_depth = int(info['bits_per_sample'])
        current_channels = int(info['channels'])
        current_format = os.path.splitext(file_path)[1][1:]

        # Check if conversion is needed
        if (current_sample_rate != self.target_sample_rate or
                current_bit_depth != self.target_bit_depth or
                current_channels != self.target_channels or
                current_format != self.target_format):
            audio = AudioSegment.from_file(file_path, format=current_format)
            audio = audio.set_frame_rate(self.target_sample_rate)
            audio = audio.set_sample_width(self.target_bit_depth // 8)
            audio = audio.set_channels(self.target_channels)

            # Determine the output file path with target format
            output_file_path = os.path.splitext(file_path)[0] + '.' + self.target_format
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

        print("WHATS_THE_MESSAGE: " + str(self.message_id))

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
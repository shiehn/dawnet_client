# Existing imports...
import json
import os
import subprocess
from .audio_utils import process_audio_file
from .dn_tracer import SentryEventLogger, DNSystemType, DNMsgStage, DNTag
from .file_uploader import FileUploader


# ResultsHandler class to handle the results
class ResultsHandler:
    def __init__(self, websocket, token, target_sample_rate=41000, target_bit_depth=16, target_channels=2, target_format="wav"):
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
        self.target_sample_rate = target_sample_rate
        self.target_bit_depth = target_bit_depth
        self.target_channels = target_channels
        self.target_format = target_format

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
            error_message = ("FFmpeg is not installed, which is required for processing audio files.\n"
                             "To install FFmpeg, follow these instructions:\n"
                             "- On macOS: Use Homebrew by running 'brew install ffmpeg' in the terminal.\n"
                             "- On Linux (Debian/Ubuntu): Run 'sudo apt-get install ffmpeg' in the terminal.\n"
                             "- On Linux (Fedora): Run 'sudo dnf install ffmpeg' in the terminal.\n"
                             "- On Linux (Arch Linux): Run 'sudo pacman -S ffmpeg' in the terminal.\n"
                             "For other operating systems or more detailed instructions, visit the FFmpeg website: https://ffmpeg.org/download.html")
            print(error_message) #TODO how do errors get reported to the user?
            self.add_error(error_message)
            return

        try:
            # Check and convert audio file if necessary
            converted_file_path = process_audio_file(
                file_path,
                target_format=self.target_format,
                target_sample_rate=self.target_sample_rate,
                target_bit_depth=self.target_bit_depth,
                target_channels=self.target_channels
            )

            print("OUTPUT_FILE: " + str(converted_file_path))

            file_url = await self.file_uploader.upload(converted_file_path, os.path.splitext(converted_file_path)[1][1:])
            self.files.append({'name': os.path.basename(converted_file_path), 'url': file_url})
        except Exception as e:
            self.dn_tracer.log_error(self.token, {
                DNTag.DNMsgStage.value: DNMsgStage.UPLOAD_ASSET.value,
                DNTag.DNMsg.value: str(e),
            })
            self.add_error(str(e))


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

def handle_the_results():
    return True
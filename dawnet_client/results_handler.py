# Existing imports...
import json
import os

from dawnet_client.file_uploader import FileUploader


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

    def update_token(self, token):
        self.token = token

    def add_error(self, error):
        self.errors.append(error)

    def set_message_id(self, message_id):
        self.message_id = message_id

    async def add_file(self, file_path, file_type):
        print('STEVE:FILE_PATH_TO_UPLOAD:' + file_path)

        # Await the coroutine and get the result
        file_url = await self.file_uploader.upload(file_path, file_type)

        print('STEVE:FILE_URL:' + file_url)
        self.files.append({'name': os.path.basename(file_path), 'type': file_type, 'url': file_url})

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
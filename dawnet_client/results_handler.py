# Existing imports...
import json
import os

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

    def update_token(self, token):
        self.token = token

    def add_error(self, error):
        self.errors.append(error)

    def set_message_id(self, message_id):
        self.message_id = message_id

    async def add_file(self, file_path, file_type):
        try:
            file_url = await self.file_uploader.upload(file_path, file_type)
            self.files.append({'name': os.path.basename(file_path), 'type': file_type, 'url': file_url})
            return
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
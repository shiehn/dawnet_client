# Existing imports...
import json


# ResultsHandler class to handle the results
class ResultsHandler:
    def __init__(self, websocket, token):
        self.websocket = websocket
        self.token = token
        self.message_id = None
        self.errors = []
        self.files = []
        self.messages = []

    def add_error(self, error):
        self.errors.append(error)

    def set_message_id(self, message_id):
        self.message_id = message_id

    def add_file(self, file_path, file_type):
        # Logic to convert the file path to a URL
        file_url = f"https://example.com/{file_path}"  # Placeholder for file URL conversion
        self.files.append({'name': file_path, 'type': file_type, 'url': file_url})

    def add_message(self, message):
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
import os


class FileTypeClassifier:
    def __init__(self):
        self.file_types = {
            'audio': ['.mp3', '.wav', '.aac', '.aif', '.aiff', '.flac', '.ogg'],
            'midi': ['.midi', '.mid'],
            'text': ['.txt', '.md', '.docx', '.pdf'],
            'video': ['.mp4', '.avi', '.mov', '.mkv'],
        }

    def classify(self, file_path):
        extension = os.path.splitext(file_path)[1].lower()
        for type, extensions in self.file_types.items():
            if extension in extensions:
                return type
        return 'other'

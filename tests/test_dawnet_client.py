import os

from dawnet_client.core import WebSocketClient

def test_process_audio_file():
    client = WebSocketClient("localhost", 8080)  # Adjust as necessary
    test_files_dir = os.path.join(os.path.dirname(__file__), "assets")

    for file in os.listdir(test_files_dir):
        if file.endswith(('.wav', '.mp3', '.aif', '.flac', '.ogg')):
            file_path = os.path.join(test_files_dir, file)

            print("INPUT FILE PATH: " + str(file_path))
            processed_file = client.process_audio_file(file_path)
            print("OUTPUT FILE PATH: " + str(processed_file))

            # Here, you can add assertions to check if the processed file meets your expectations
            # For example, check the sample rate, bit depth, and channels of the processed file

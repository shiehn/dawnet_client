import os

from dawnet_client.core import WebSocketClient
import os
import wave
import aifc
import soundfile as sf
from pydub.utils import mediainfo

import os
import wave
import aifc
from pydub.utils import mediainfo

def test_process_audio_file():
    client = WebSocketClient("localhost", 8080)  # Adjust as necessary
    test_files_dir = os.path.join(os.path.dirname(__file__), "assets")
    output_formats = ['wav', 'aif', 'mp3', 'flac']
    sample_rates = [22050, 32000, 44100, 48000]

    for file in os.listdir(test_files_dir):
        if file.endswith(('.wav', '.mp3', '.aif', '.flac', '.ogg')):
            file_path = os.path.join(test_files_dir, file)

            for format in output_formats:
                for sample_rate in sample_rates:
                    client.input_format = format  # Set output format
                    client.input_sample_rate = sample_rate
                    client.input_bit_depth = 16
                    client.input_channels = 2

                    print(f"\nTesting file: {file_path}")
                    print(f"Input Specs - Format: {format}, Sample Rate: {sample_rate}, Bit Depth: {client.input_bit_depth}, Channels: {client.input_channels}")

                    processed_file = client.process_audio_file(file_path)

                    # Determine the format and get the specifications
                    file_extension = os.path.splitext(processed_file)[1].lower()
                    if file_extension in ['.wav', '.aif']:
                        opener = wave.open if file_extension == '.wav' else aifc.open
                        with opener(processed_file, 'rb') as f:
                            channels = f.getnchannels()
                            actual_sample_rate = f.getframerate()
                            bit_depth = f.getsampwidth() * 8
                    elif file_extension in ['.mp3', '.flac']:
                        info = mediainfo(processed_file)
                        channels = int(info['channels']) if file_extension != '.flac' else client.input_channels
                        actual_sample_rate = int(info['sample_rate'])
                        bit_depth = int(info.get('bits_per_sample') or client.input_bit_depth) if file_extension != '.mp3' else client.input_bit_depth

                    print(f"Output Specs - File: {processed_file}, Sample Rate: {actual_sample_rate}, Bit Depth: {bit_depth}, Channels: {channels}")

                    # Assertions to ensure specifications match
                    assert actual_sample_rate == sample_rate, f"Sample rate mismatch for format {format} and sample rate {sample_rate}: expected {sample_rate}, got {actual_sample_rate}"
                    if file_extension not in ['.mp3', '.flac']:
                        assert bit_depth == client.input_bit_depth, f"Bit depth mismatch for format {format}: expected {client.input_bit_depth}, got {bit_depth}"
                        assert channels == client.input_channels, f"Channel count mismatch for format {format}: expected {client.input_channels}, got {channels}"
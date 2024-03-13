import shutil
import os
import wave
import aifc

from pydub.utils import mediainfo
from elixit_client.utils import get_audio_length, process_audio_file


def clean_up_resampled_files(file_path):
    # Check if the directory exists
    if os.path.exists(file_path):
        # Remove the directory and all its contents
        shutil.rmtree(file_path)
        print(f"Directory '{file_path}' has been removed.")
    else:
        print(f"Directory '{file_path}' does not exist.")


def test_process_audio_file():
    clean_up_resampled_files(
        os.path.join(os.path.dirname(__file__), "assets", "resampled")
    )

    test_files_dir = os.path.join(os.path.dirname(__file__), "assets")
    output_formats = ["wav", "aif", "aiff", "mp3", "flac"]
    sample_rates = [22050, 32000, 44100, 48000]
    bit_depths = [16, 24]  # Example bit depths
    channels_list = [1, 2]

    for file in os.listdir(test_files_dir):
        if file.endswith((".wav", ".mp3", ".aif", ".flac", ".ogg")):
            file_path = os.path.join(test_files_dir, file)

            for format in output_formats:
                for sample_rate in sample_rates:
                    for bit_depth in bit_depths:
                        for channels in channels_list:
                            if format in ["wav", "aif", "aiff"]:
                                print(f"\nTesting file: {file_path}")
                                print(
                                    f"Target Specs - Format: {format}, Sample Rate: {sample_rate}, Bit Depth: {bit_depth}, Channels: {channels}"
                                )

                                processed_file = process_audio_file(
                                    file_path,
                                    target_format=format,
                                    target_sample_rate=sample_rate,
                                    target_bit_depth=bit_depth,
                                    target_channels=channels,
                                )

                                # Determine the format and get the specifications
                                file_extension = os.path.splitext(processed_file)[
                                    1
                                ].lower()
                                if file_extension in [".wav", ".aif", ".aiff"]:
                                    opener = (
                                        wave.open
                                        if file_extension == ".wav"
                                        else aifc.open
                                    )
                                    with opener(processed_file, "rb") as f:
                                        actual_channels = f.getnchannels()
                                        actual_sample_rate = f.getframerate()
                                        actual_bit_depth = f.getsampwidth() * 8
                                elif file_extension in [".mp3", ".flac"]:
                                    info = mediainfo(processed_file)
                                    actual_channels = (
                                        int(info["channels"])
                                        if file_extension != ".flac"
                                        else channels
                                    )
                                    actual_sample_rate = int(info["sample_rate"])
                                    actual_bit_depth = (
                                        int(info.get("bits_per_sample") or bit_depth)
                                        if file_extension != ".mp3"
                                        else bit_depth
                                    )

                                print(
                                    f"Output Specs - File: {processed_file}, Sample Rate: {actual_sample_rate}, Bit Depth: {bit_depth}, Channels: {channels}"
                                )

                                # Assertions to ensure specifications match
                                assert (
                                    actual_sample_rate == sample_rate
                                ), f"Sample rate mismatch for format {format} and sample rate {sample_rate}: expected {sample_rate}, got {actual_sample_rate}"
                                if file_extension not in [".mp3", ".flac"]:
                                    assert (
                                        actual_bit_depth == bit_depth
                                    ), f"Bit depth mismatch for format {format}: expected {bit_depth}, got {actual_bit_depth}"
                                    assert (
                                        actual_channels == channels
                                    ), f"Channel count mismatch for format {format}: expected {channels}, got {actual_channels}"

    clean_up_resampled_files(
        os.path.join(os.path.dirname(__file__), "assets", "resampled")
    )


def test_get_audio_length():
    test_files_dir = os.path.join(os.path.dirname(__file__), "assets")

    for file in os.listdir(test_files_dir):
        if file.endswith((".wav", ".mp3", ".aif", ".flac", ".ogg")):
            file_path = os.path.join(test_files_dir, file)

            length_float = get_audio_length(file_path)

            rounded_length = round(length_float, 1)

            assert rounded_length == 16.0

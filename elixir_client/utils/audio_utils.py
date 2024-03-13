import os
import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment


def process_audio_file(
    file_path: str,
    target_format: str = "wav",
    target_sample_rate: int = 44100,
    target_bit_depth: int = 16,
    target_channels: int = 2,
):
    # Create 'resampled' directory if it doesn't exist
    resampled_dir = os.path.join(os.path.dirname(file_path), "resampled")
    if not os.path.exists(resampled_dir):
        os.makedirs(resampled_dir)

    # Set the output file extension and format
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file_extension = target_format.lower()
    output_file_path = os.path.join(
        resampled_dir, f"{base_name}.{output_file_extension}"
    )
    output_format = (
        "AIFF" if output_file_extension in ["aif", "aiff"] else output_file_extension
    )

    # Set the subtype for bit depth (specific for WAV and AIFF)
    subtype = "PCM_16"  # default
    if output_file_extension in ["wav", "aif", "aiff"]:
        subtype = f"PCM_{target_bit_depth}" if target_bit_depth in [16, 24] else subtype

    # Load and process the audio file
    y, sr = librosa.load(
        file_path, sr=None, mono=False
    )  # Load with original sample rate and preserve channels
    y = librosa.resample(y, orig_sr=sr, target_sr=target_sample_rate)  # Resample

    # Handle stereo or mono conversion
    if target_channels == 1:
        y = librosa.to_mono(y)
    elif target_channels == 2 and y.ndim == 1:
        y = np.vstack([y, y])

    # Convert to target bit depth
    if target_bit_depth == 16:
        y = (y * np.iinfo(np.int16).max).astype(np.int16)
    elif target_bit_depth == 24:
        # Process as 32-bit but write as 24-bit
        y = (y * np.iinfo(np.int32).max).astype(np.int32)

    # Write the audio file
    sf.write(
        output_file_path, y.T, target_sample_rate, format=output_format, subtype=subtype
    )

    # Verify the result
    # processed_audio = AudioSegment.from_file(output_file_path)
    # assert processed_audio.frame_rate == target_sample_rate, f"Sample rate conversion failed: expected {target_sample_rate}, got {processed_audio.frame_rate}"
    # assert processed_audio.channels == target_channels, f"Channel conversion failed: expected {target_channels}, got {processed_audio.channels}"
    # assert processed_audio.sample_width * 8 in [target_bit_depth, 32], f"Bit depth conversion failed: expected {target_bit_depth} or 32, got {processed_audio.sample_width * 8}"

    return output_file_path


def get_audio_length(file_path: str) -> float:
    """
    Returns the length of the audio file in seconds.

    :param file_path: Path to the audio file
    :return: Length of the audio in seconds
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_file(file_path)

        # Calculate the length in seconds
        length_seconds = len(audio) / 1000.0
        return length_seconds
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

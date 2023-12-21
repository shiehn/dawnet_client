import uuid

import pytest
from unittest.mock import patch, MagicMock
import dawnet_client


# Mock class to replace WebSocketClient
class MockWebSocketClient:
    def __init__(self, server_ip, server_port):
        self.input_format = None
        self.input_bit_depth = None
        self.input_sample_rate = None
        self.input_channels = None

        self.output_sample_rate = None
        self.output_bit_depth = None
        self.output_channels = None
        self.output_format = None

        self.dawnet_token = None
    # You might need to add mock methods here if they are called in your tests


# Patching the WebSocketClient class in dawnet_client.core module
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_format_valid():
    dawnet_client.set_input_target_format("mp3")
    assert dawnet_client.core._client.input_format == "mp3"


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_format_invalid():
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_input_target_format("abc")
    assert "Invalid format: 'abc'" in str(excinfo.value)


# Patching the WebSocketClient class in dawnet_client.core module
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_bit_depth_valid():
    # Test for valid bit depth 16
    dawnet_client.set_input_target_bit_depth(16)
    assert dawnet_client.core._client.input_bit_depth == 16

    # Test for valid bit depth 24
    dawnet_client.set_input_target_bit_depth(24)
    assert dawnet_client.core._client.input_bit_depth == 24


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_bit_depth_invalid():
    # Test for invalid bit depth
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_input_target_bit_depth(8)  # Assuming 8 is an invalid bit depth
    assert "Invalid bit depth: '8'" in str(excinfo.value)


# Patching the WebSocketClient class in dawnet_client.core module
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_sample_rate_valid():
    # Test for valid sample rates
    for rate in [22050, 32000, 44100, 48000]:
        dawnet_client.set_input_target_sample_rate(rate)
        assert dawnet_client.core._client.input_sample_rate == rate


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_sample_rate_invalid():
    # Test for invalid sample rate
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_input_target_sample_rate(16000)  # Assuming 16000 is an invalid sample rate
    assert "Invalid sample rate: '16000'" in str(excinfo.value)


# Patching the WebSocketClient class in dawnet_client.core module
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_channels_valid():
    # Test for valid channel counts
    for channels in [1, 2]:
        dawnet_client.set_input_target_channels(channels)
        assert dawnet_client.core._client.input_channels == channels


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_input_target_channels_invalid():
    # Test for invalid channel count
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_input_target_channels(3)  # Assuming 3 is an invalid channel count
    assert "Invalid channel count: '3'" in str(excinfo.value)


# Patching the WebSocketClient class in dawnet_client.core module
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_token_valid():
    # Generate a valid UUID4 token
    valid_uuid4 = str(uuid.uuid4())
    dawnet_client.set_token(valid_uuid4)
    assert dawnet_client.core._client.dawnet_token == valid_uuid4


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_token_invalid():
    # Test with an invalid token
    invalid_token = "12345"
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_token(invalid_token)
    assert f"Invalid token: '{invalid_token}'" in str(excinfo.value)


# Test for set_output_target_sample_rate
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_sample_rate_valid():
    for rate in [22050, 32000, 44100, 48000]:
        dawnet_client.set_output_target_sample_rate(rate)
        assert dawnet_client.core._client.output_sample_rate == rate


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_sample_rate_invalid():
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_output_target_sample_rate(16000)  # Assuming 16000 is an invalid sample rate
    assert "Invalid output sample rate: '16000'. Valid rates: [22050, 32000, 44100, 48000]" in str(excinfo.value)


# Test for set_output_target_bit_depth
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_bit_depth_valid():
    for depth in [16, 24]:
        dawnet_client.set_output_target_bit_depth(depth)
        assert dawnet_client.core._client.output_bit_depth == depth


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_bit_depth_invalid():
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_output_target_bit_depth(8)
    assert "Invalid output bit depth: '8'. Valid depths: [16, 24]" in str(excinfo.value)


# Test for set_output_target_channels
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_channels_valid():
    for channels in [1, 2]:
        dawnet_client.set_output_target_channels(channels)
        assert dawnet_client.core._client.output_channels == channels


@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_channels_invalid():
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_output_target_channels(3)  # Assuming 3 is an invalid channel count
    assert "Invalid output channel count: '3'. Valid counts: [1, 2]" in str(excinfo.value)


# Test for set_output_target_format
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_format_valid():
    dawnet_client.set_output_target_format("mp3")
    assert dawnet_client.core._client.output_format == "mp3"


# Test for set_output_target_format
@patch('dawnet_client.core.WebSocketClient', new=MockWebSocketClient)
def test_set_output_target_format_invalid():
    with pytest.raises(ValueError) as excinfo:
        dawnet_client.set_output_target_format("abc")
    assert "Invalid output format: 'abc'. Valid formats: ['wav', 'mp3', 'aif', 'aiff', 'flac']" in str(excinfo.value)


def test_it_gives_me_42():
    assert dawnet_client.utils.give_me_a_number() == 42


def test_results():
    assert dawnet_client.output.handle_the_results() is True

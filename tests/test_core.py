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

    # Test for valid bit depth 32
    dawnet_client.set_input_target_bit_depth(32)
    assert dawnet_client.core._client.input_bit_depth == 32

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
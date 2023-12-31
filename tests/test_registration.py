import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock
from dawnet_client import WebSocketClient, DAWNetFilePath
from dawnet_client import ui_param


# Example method to register
async def example_method_one(a: int, b: float, c: str, d: DAWNetFilePath):
    pass

@pytest.mark.asyncio
async def test_register_method_one():
    # SETUP
    client = WebSocketClient('127.0.0.1', '1234')
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method('example_method_one', example_method_one)

    # ASSERTS
    client.connect.assert_called_once()
    assert 'example_method_one' in client.method_details
    assert client.method_details['example_method_one']['params'] == [
        {'name': 'a', 'type': 'int', 'default_value': None, 'ui_component': None},
        {'name': 'b', 'type': 'float', 'default_value': None, 'ui_component': None},
        {'name': 'c', 'type': 'str', 'default_value': None, 'ui_component': None},
        {'name': 'd', 'type': 'DAWNetFilePath', 'default_value': None, 'ui_component': None}]

async def example_method_one_defaults(a: int=5, b: float=2.2, c: str='hello', d: DAWNetFilePath=None):
    pass

@pytest.mark.asyncio
async def test_register_method_one_defaults():
    # SETUP
    client = WebSocketClient('127.0.0.1', '1234')
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method('example_method_one_defaults', example_method_one_defaults)

    # ASSERTS
    client.connect.assert_called_once()
    assert 'example_method_one_defaults' in client.method_details
    assert client.method_details['example_method_one_defaults']['params'] == [
        {'name': 'a', 'type': 'int', 'default_value': 5, 'ui_component': None},
        {'name': 'b', 'type': 'float', 'default_value': 2.2, 'ui_component': None},
        {'name': 'c', 'type': 'str', 'default_value': 'hello', 'ui_component': None},
        {'name': 'd', 'type': 'DAWNetFilePath', 'default_value': None, 'ui_component': None}
    ]

async def example_method_one_partial_defaults(a: int, b: float, c: str='hello', d: DAWNetFilePath=None):
    pass

@pytest.mark.asyncio
async def test_method_one_partial_defaults():
    # SETUP
    client = WebSocketClient('127.0.0.1', '1234')
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method('example_method_one_partial_defaults', example_method_one_partial_defaults)

    # ASSERTS
    client.connect.assert_called_once()
    assert 'example_method_one_partial_defaults' in client.method_details
    assert client.method_details['example_method_one_partial_defaults']['params'] == [
        {'name': 'a', 'type': 'int', 'default_value': None, 'ui_component': None},
        {'name': 'b', 'type': 'float', 'default_value': None, 'ui_component': None},
        {'name': 'c', 'type': 'str', 'default_value': 'hello', 'ui_component': None},
        {'name': 'd', 'type': 'DAWNetFilePath', 'default_value': None, 'ui_component': None}
    ]

@ui_param('a', 'DAWNetNumberSlider', min=0, max=10, step=1, default=5)
async def example_method_one_with_decorators(a: int, b: float, c: str='hello', d: DAWNetFilePath=None):
    pass

@pytest.mark.asyncio
async def test_register_method_one_with_decorators():
    # SETUP
    client = WebSocketClient('127.0.0.1', '1234')
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method('example_method_one_with_decorators', example_method_one_with_decorators)

    # ASSERTS
    client.connect.assert_called_once()
    assert 'example_method_one_with_decorators' in client.method_details
    assert client.method_details['example_method_one_with_decorators']['params'] == [
        {'name': 'a', 'type': 'int', 'default_value': 5, 'min': 0, 'max': 10, 'step': 1, 'ui_component': 'DAWNetNumberSlider'},
        {'name': 'b', 'type': 'float', 'default_value': None, 'ui_component': None},
        {'name': 'c', 'type': 'str', 'default_value': 'hello', 'ui_component': None},
        {'name': 'd', 'type': 'DAWNetFilePath', 'default_value': None, 'ui_component': None}
    ]

import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock
from elixit_client import WebSocketClient, DAWNetFilePath
from elixit_client import ui_param


# Example method to register
async def example_method_one(a: int, b: float, c: str, d: DAWNetFilePath):
    pass


@pytest.mark.asyncio
async def test_register_method_one():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_one)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one" in client.method_details
    assert client.method_details["example_method_one"]["params"] == [
        {"name": "a", "type": "int", "default_value": 0, "ui_component": None},
        {"name": "b", "type": "float", "default_value": 0.0, "ui_component": None},
        {"name": "c", "type": "str", "default_value": "", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]

    assert client.master_token != None
    assert client.dawnet_token != None
    assert client.dawnet_token != client.master_token


@pytest.mark.asyncio
async def test_register_method_one_with_no_name_no_description():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_one)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one" in client.method_details
    assert client.method_details["example_method_one"]["params"] == [
        {"name": "a", "type": "int", "default_value": 0, "ui_component": None},
        {"name": "b", "type": "float", "default_value": 0.0, "ui_component": None},
        {"name": "c", "type": "str", "default_value": "", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]

    assert client.method_details["example_method_one"]["name"] == "Default Name"
    assert (
        client.method_details["example_method_one"]["description"]
        == "Default Description"
    )

    assert client.master_token != None
    assert client.dawnet_token != None
    assert client.dawnet_token != client.master_token


@pytest.mark.asyncio
async def test_register_method_one_with_description():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    client.set_name("My Special Method")
    client.set_description("My Special Method Description")

    # EXECUTE
    await client.register_method(example_method_one)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one" in client.method_details
    assert client.method_details["example_method_one"]["params"] == [
        {"name": "a", "type": "int", "default_value": 0, "ui_component": None},
        {"name": "b", "type": "float", "default_value": 0.0, "ui_component": None},
        {"name": "c", "type": "str", "default_value": "", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]

    assert client.method_details["example_method_one"]["name"] == "My Special Method"
    assert (
        client.method_details["example_method_one"]["description"]
        == "My Special Method Description"
    )
    assert client.master_token != None
    assert client.dawnet_token != None
    assert client.dawnet_token != client.master_token


async def example_method_one_defaults(
    a: int = 5, b: float = 2.2, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_register_method_one_defaults():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_one_defaults)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one_defaults" in client.method_details
    assert client.method_details["example_method_one_defaults"]["params"] == [
        {"name": "a", "type": "int", "default_value": 5, "ui_component": None},
        {"name": "b", "type": "float", "default_value": 2.2, "ui_component": None},
        {"name": "c", "type": "str", "default_value": "hello", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]


async def example_method_one_partial_defaults(
    a: int, b: float, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_method_one_partial_defaults():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_one_partial_defaults)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one_partial_defaults" in client.method_details
    assert client.method_details["example_method_one_partial_defaults"]["params"] == [
        {"name": "a", "type": "int", "default_value": 0, "ui_component": None},
        {"name": "b", "type": "float", "default_value": 0.0, "ui_component": None},
        {"name": "c", "type": "str", "default_value": "hello", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]


@ui_param("a", "DAWNetNumberSlider", min=0, max=10, step=1, default=5)
async def example_method_one_with_decorators(
    a: int, b: float, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_register_method_one_with_decorators():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_one_with_decorators)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one_with_decorators" in client.method_details
    assert client.method_details["example_method_one_with_decorators"]["params"] == [
        {
            "name": "a",
            "type": "int",
            "default_value": 5,
            "min": 0,
            "max": 10,
            "step": 1,
            "ui_component": "DAWNetNumberSlider",
        },
        {"name": "b", "type": "float", "default_value": 0.0, "ui_component": None},
        {"name": "c", "type": "str", "default_value": "hello", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]


@ui_param("a", "DAWNetNumberSlider", min=0, max=10, step=1, default=5)
@ui_param("b", "DAWNetNumberSlider", min=0.0, max=10.0, step=0.5, default=7.7)
async def example_method_one_with_multiple_decorators(
    a: int, b: float = 7.7, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_register_method_one_with_multiple_decorators():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_one_with_multiple_decorators)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_one_with_multiple_decorators" in client.method_details
    assert client.method_details["example_method_one_with_multiple_decorators"][
        "params"
    ] == [
        {
            "name": "a",
            "type": "int",
            "default_value": 5,
            "min": 0,
            "max": 10,
            "step": 1,
            "ui_component": "DAWNetNumberSlider",
        },
        {
            "name": "b",
            "type": "float",
            "default_value": 7.7,
            "min": 0.0,
            "max": 10.0,
            "step": 0.5,
            "ui_component": "DAWNetNumberSlider",
        },
        {"name": "c", "type": "str", "default_value": "hello", "ui_component": None},
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]


@ui_param("a", "unsupported_ui_component", min=0, max=10, step=1, default=5)
async def example_method_one_with_unsupported_decorators(
    a: int, b: float, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_register_method_one_with_unsupported_decorators():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE and ASSERT
    with pytest.raises(ValueError) as exc_info:
        await client.register_method(example_method_one_with_unsupported_decorators)

    assert "Unsupported UI component" in str(exc_info.value)


@ui_param("a", "DAWNetNumberSlider", min=0, max=10, fakeparam="fake", step=1, default=5)
async def example_method_one_with_unsupported_param(
    a: int, b: float, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_register_method_one_with_unsupported_param():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE and ASSERT
    with pytest.raises(ValueError) as exc_info:
        await client.register_method(example_method_one_with_unsupported_param)

    assert "Unsupported UI param" in str(exc_info.value)


@ui_param("a", "DAWNetNumberSlider", min=0, max=10, default=5)
async def example_method_one_missing_required_param(
    a: int, b: float, c: str = "hello", d: DAWNetFilePath = None
):
    pass


@pytest.mark.asyncio
async def test_register_method_one_missing_required_param():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE and ASSERT
    with pytest.raises(ValueError) as exc_info:
        await client.register_method(example_method_one_missing_required_param)

    assert "Missing required param(s)" in str(exc_info.value)


@ui_param("c", "DAWNetMultiChoice", options=["one", "two", "three"], default="two")
async def example_method_multichoice(a: int, b: float, c: str, d: DAWNetFilePath):
    pass


@pytest.mark.asyncio
async def test_register_method_example_method_multichoice():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_multichoice)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_multichoice" in client.method_details
    assert client.method_details["example_method_multichoice"]["params"] == [
        {"name": "a", "type": "int", "ui_component": None, "default_value": 0},
        {"name": "b", "type": "float", "ui_component": None, "default_value": 0.0},
        {
            "name": "c",
            "type": "str",
            "options": ["one", "two", "three"],
            "default_value": "two",
            "ui_component": "DAWNetMultiChoice",
        },
        {
            "name": "d",
            "type": "DAWNetFilePath",
            "default_value": None,
            "ui_component": None,
        },
    ]


async def example_method_with_bool_no_default(a: bool):
    pass


@pytest.mark.asyncio
async def test_register_method_example_method_with_bool_no_default():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_with_bool_no_default)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_with_bool_no_default" in client.method_details
    assert client.method_details["example_method_with_bool_no_default"]["params"] == [
        {"name": "a", "type": "bool", "ui_component": None, "default_value": False}
    ]


async def example_method_with_bool_default_True(a: bool = True):
    pass


@pytest.mark.asyncio
async def test_register_method_example_method_with_bool_default_True():
    # SETUP
    client = WebSocketClient("127.0.0.1", "1234")
    client.connect = AsyncMock()
    client.set_token(str(uuid.uuid4()))

    # EXECUTE
    await client.register_method(example_method_with_bool_default_True)

    # ASSERTS
    client.connect.assert_called_once()
    assert "example_method_with_bool_default_True" in client.method_details
    assert client.method_details["example_method_with_bool_default_True"]["params"] == [
        {"name": "a", "type": "bool", "ui_component": None, "default_value": True}
    ]

# test_results_handler.py
import pytest
from elixit_client.output.results_handler import ResultsHandler


def test_clear_outputs():
    # Create an instance of ResultsHandler
    handler = ResultsHandler("websocket", "token")

    # Modify its attributes
    handler.message_id = "some_message_id"
    handler.errors = ["error1", "error2"]
    handler.files = ["file1", "file2"]
    handler.messages = ["message1", "message2"]

    # Call clear_outputs
    handler.clear_outputs()

    # Assert that the attributes are reset to their initial state
    assert handler.message_id is None
    assert handler.errors == []
    assert handler.files == []
    assert handler.messages == []

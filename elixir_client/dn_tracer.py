import logging
from enum import Enum
from typing import Any, Dict
from threading import Thread

from .config import SENTRY_API_KEY
import sentry_sdk


class DNTag(Enum):
    DNToken = "dn_token"
    DNSystemType = "dn_system"
    DNMsgType = "dn_msg_type"
    DNMsgStage = "dn_msg_stage"
    DNMsg = "dn_msg"


class DNSystemType(Enum):
    DN_PLUGIN = "DN_PLUGIN"
    DN_DISCOVERY_SERVER = "DN_DISCOVERY_SERVER"
    DN_API_SERVER = "DN_API_SERVER"
    DN_CLIENT = "DN_CLIENT"


class DNMsgType(Enum):
    DN_ERROR = "DN_ERROR"
    DN_EVENT = "DN_EVENT"


class DNMsgStage(Enum):
    SET_MSG_PENDING = "UPDATE_MSG_PENDING"
    REPLY_TO_MSG = "REPLY_TO_MSG"
    UPDATE_MSG_STATUS = "UPDATE_MSG_STATUS"
    ABORT_MSG = "ABORT_MSG"
    SAVE_CONTRACT = "SAVE_CONTRACT"
    UPLOAD_ASSET = "UPLOAD_ASSET"
    CLIENT_CONNECTION = "CLIENT_CONNECTION"
    CLIENT_REG_CONTRACT = "CLIENT_REG_CONTRACT"
    CLIENT_REG_METHOD = "CLIENT_REG_METHOD"
    CLIENT_RUN_METHOD = "CLIENT_RUN_METHOD"
    CLIENT_DOWNLOAD_ASSET = "CLIENT_DOWNLOAD_ASSET"
    CLIENT_UPLOAD_ASSET = "CLIENT_UPLOAD_ASSET"
    CLIENT_CONVERT_DOWNLOAD = "CLIENT_CONVERT_DOWNLOAD"
    CLIENT_CONVERT_UPLOAD = "CLIENT_CONVERT_UPLOAD"
    CLIENT_SEND_RESULTS_MSG = "CLIENT_SEND_RESULTS_MSG"
    WS_RECEIVE_MSG = "WS_RECEIVE_MSG"
    WS_REG_TOKEN = "WS_REG_TOKEN"
    WS_REG_CONTRACT = "WS_REG_CONTRACT"
    WS_SEND_RESULTS = "WS_SEND_RESULTS"
    WS_UN_REG_TOKEN = "WS_UN_REG_TOKEN"


def before_send(event, hint):
    # Check if the event has tags and the specific tag 'dn_token'
    if "tags" in event:
        dn_token = event["tags"].get("dn_token")
        if dn_token and dn_token.strip() != "":
            return event  # Send the event as it contains 'dn_token' and it's not empty
    # If 'dn_token' is not present or empty, do not send the event
    return None


def traces_sampler(sampling_context):
    # Access transaction context to check its name
    transaction_context = sampling_context.get("transaction_context", {})
    transaction_name = transaction_context.get("name")

    # Sample only if the transaction is named 'customer.event'
    if transaction_name == "customer.event":
        return 1  # Send the transaction to Sentry
    else:
        return 0  # Do not send the transaction


# Initialize Sentry
sentry_sdk.init(
    dsn=SENTRY_API_KEY,
    # Set traces_sample_rate to 0 to disable automatic performance monitoring
    # traces_sample_rate=1,
    traces_sampler=traces_sampler,
    # before_send=before_send
)


class SentryEventLogger:
    def __init__(self, service_name: str = "system-type-not-set") -> None:
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)

    def log_event(self, dn_token: str, event_info: Dict[str, Any]) -> None:
        thread = Thread(
            target=self._handle_event,
            args=(dn_token, DNMsgType.DN_EVENT.value, event_info),
        )
        thread.start()

    def log_error(self, dn_token: str, event_info: Dict[str, Any]) -> None:
        thread = Thread(
            target=self._handle_event,
            args=(dn_token, DNMsgType.DN_ERROR.value, event_info),
        )
        thread.start()

    def _handle_event(
        self, dn_token: str, dn_msg_type: str, event_info: Dict[str, Any]
    ) -> None:
        self._process_event(event_info)
        return

    #         with start_transaction(op="task", name="customer.event") as transaction:
    #             # Set a custom UUID as a tag
    #             transaction.set_tag(DNTag.DNToken.value, str(dn_token))
    #             transaction.set_tag(DNTag.DNSystemType.value, self.service_name)
    #             transaction.set_tag(DNTag.DNMsgType.value, dn_msg_type)
    #
    #             for key, value in event_info.items():
    #                 transaction.set_tag(key, value)
    #
    #             self._process_event(event_info)
    #             transaction.set_data("event_info", event_info)
    #             transaction.sampled = True

    def _process_event(self, event_info: Dict[str, Any]) -> None:
        self.logger.info(f"Processing event: {event_info}")


# Example usage
# event_logger = SentryEventLogger()
# event_info = {"type": "purchase", "customer_id": "12345"}
# custom_uuid = "123e4567-e89b-12d3-a456-426614174000"  # Replace with your custom UUID
# event_logger.log_event(custom_uuid, event_info)

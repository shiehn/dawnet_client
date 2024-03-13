import asyncio
import io
import sys
import uuid

import websockets
import nest_asyncio
import json
import logging
import os
import tempfile
import aiohttp

from .utils import process_audio_file
from .output import ResultsHandler
from .config import SOCKET_IP, SOCKET_PORT
from .dn_tracer import SentryEventLogger, DNSystemType, DNTag, DNMsgStage
from inspect import signature, Parameter

# Apply nest_asyncio to allow nested running of event loops
nest_asyncio.apply()

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class RunStatus:
    def __init__(self):
        self.status = "idle"


run_status = RunStatus()

# Method registry for the client
method_registry_local = {}
method_details_local = {}


class WebSocketClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.websocket = None
        self.method_registry = {}
        self.method_details = {}
        self.run_status = "idle"
        self.dawnet_token = None
        self.master_token = None
        self.message_id = None
        self.results = None
        self.author = "Default Author"
        self.name = "Default Name"
        self.description = "Default Description"
        self.version = "0.0.0"
        self.logger = logging.getLogger(__name__)
        self.dn_tracer = SentryEventLogger(service_name=DNSystemType.DN_CLIENT.value)

        # Default input target audio settings
        self.input_sample_rate = 44100
        self.input_bit_depth = 16
        self.input_channels = 2
        self.input_format = "wav"  # "wav", "mp3", "aif", "flac"

        # Default output target audio settings
        self.output_sample_rate = 44100
        self.output_bit_depth = 16
        self.output_channels = 2
        self.output_format = "wav"  # "wav", "mp3", "aif", "flac"

        # DAW SESSION INFO
        self.daw_bpm = 0
        self.daw_sample_rate = 0

        # Check if DN_CLIENT_TOKEN environment variable is set and non-empty
        dn_client_token = os.getenv("DN_CLIENT_TOKEN")
        if dn_client_token:
            self.master_token = dn_client_token

    async def send_registered_methods_to_server(self):
        if self.dawnet_token is None:
            raise Exception(
                "Token not set. Please call set_token(token) before calling send_registered_methods_to_server()."
            )

        if self.master_token is None:
            raise Exception(
                "Master Token not set. Please call set_token(token) before calling send_registered_methods_to_server()."
            )

        await self.connect()  # Ensure we're connected

        # Check if there's at least one method registered
        if self.method_registry:
            # Get the last registered method's name and details
            last_method_name, last_method = next(reversed(self.method_registry.items()))
            last_method_details = self.method_details[last_method_name]

            # Construct the message to register the method
            register_compute_contract_msg = {
                "token": self.dawnet_token,
                "type": "contract",
                "data": last_method_details,
            }

            # Send the registration message to the server
            await self.websocket.send(json.dumps(register_compute_contract_msg))
            self.dn_tracer.log_event(
                self.dawnet_token,
                {
                    DNTag.DNMsgStage.value: DNMsgStage.CLIENT_REG_CONTRACT.value,
                    DNTag.DNMsg.value: f"Sent contract for registration. Token: {self.dawnet_token}",
                },
            )

    async def connect(self):
        if self.websocket is None or self.websocket.closed:
            uri = f"ws://{self.server_ip}:{self.server_port}"
            self.websocket = await websockets.connect(uri)
            self.dn_tracer.log_event(
                self.dawnet_token,
                {
                    DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                    DNTag.DNMsg.value: f"Connected to {uri}",
                },
            )
            self.results = ResultsHandler(
                websocket=self.websocket,
                token=self.dawnet_token,
                target_sample_rate=self.output_sample_rate,
                target_bit_depth=self.output_bit_depth,
                target_channels=self.output_channels,
                target_format=self.output_format,
            )

        try:
            await self.register_compute_instance()
        except Exception as e:
            self.dn_tracer.log_error(
                self.dawnet_token,
                {
                    DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                    DNTag.DNMsg.value: f"Error connecting. {e}",
                },
            )

    async def register_compute_instance(self):
        if self.dawnet_token is None:
            raise Exception(
                "Token not set. Please call set_token(token) before registering a method."
            )

        if self.master_token is None:
            raise Exception(
                "Master Token not set. Please call set_token(token) before registering a method."
            )

        # Construct the message to register the compute instance
        register_compute_instance_msg = {
            "token": self.dawnet_token,
            "type": "register",
            "data": {
                "master_token": self.master_token,
                "name": self.name,
                "description": self.description,
                "status": 1,  # Assuming 'status': 1 indicates a successful registration
            },
        }

        # Send the registration message to the server
        await self.websocket.send(json.dumps(register_compute_instance_msg))

    async def validate_and_process_parameters(self, method):
        params = []
        param_names = set()
        sig = signature(method)
        max_param_count = 12
        max_param_name_length = 36

        if len(sig.parameters) > max_param_count:
            raise ValueError("Method cannot have more than 12 parameters.")

        for param in sig.parameters.values():
            if len(param.name) > max_param_name_length:
                raise ValueError(
                    f"Parameter name '{param.name}' exceeds 36 characters."
                )

            if param.name in param_names:
                raise ValueError(f"Duplicate parameter name '{param.name}' detected.")
            param_names.add(param.name)

            if param.annotation is Parameter.empty:
                raise ValueError(
                    f"Parameter '{param.name}' is missing a type annotation."
                )

            param_type_name = param.annotation.__name__
            supported_types = {"bool", "int", "float", "str", "DAWNetFilePath"}
            if param_type_name not in supported_types:
                raise ValueError(
                    f"Unsupported type '{param_type_name}' for parameter '{param.name}'."
                )

            default_value = None if param.default is Parameter.empty else param.default
            default_value = await self.set_default_for_types(
                default_value, param_type_name
            )

            ui_component_details = self.process_ui_components(method, param)
            param_info = {
                "name": param.name,
                "type": param_type_name,
                "default_value": default_value,
            }
            param_info.update(ui_component_details)

            params.append(param_info)

        return params

    def process_ui_components(self, method, param):
        ui_component_details = {"ui_component": None}
        supported_ui_param_keys = {
            "min",
            "max",
            "step",
            "default",
            "ui_component",
            "options",
        }
        supported_ui_components = {"DAWNetNumberSlider", "DAWNetMultiChoice"}
        ui_component_requirements = {
            "dawnetnumberslider": {"min", "max", "step", "default"},
            "dawnetmultichoice": {"options", "default"},
        }

        if hasattr(method, "_ui_params") and param.name in method._ui_params:
            ui_param_info = method._ui_params[param.name]

            for key in ui_param_info.keys():
                if key not in supported_ui_param_keys:
                    raise ValueError(
                        f"Unsupported UI param '{key}' for parameter '{param.name}'."
                    )

            if "ui_component" in ui_param_info:
                ui_component = ui_param_info["ui_component"].lower()
                required_params = ui_component_requirements.get(ui_component, set())
                missing_params = required_params - set(
                    key.lower() for key in ui_param_info.keys()
                )
                if missing_params:
                    raise ValueError(
                        f"Missing required param(s) {missing_params} for UI component '{ui_component}' in parameter '{param.name}'."
                    )

                if ui_component not in {
                    comp.lower() for comp in supported_ui_components
                }:
                    raise ValueError(
                        f"Unsupported UI component '{ui_component}' for parameter '{param.name}'."
                    )

                ui_component_details["ui_component"] = ui_component
                ui_component_details.update(
                    {k: v for k, v in ui_param_info.items() if k != "default"}
                )

            if "default" in ui_param_info:
                ui_component_details["default_value"] = ui_param_info["default"]

        return ui_component_details

    def create_json_payload(self, method_name, params):
        method_details = {
            "method_name": method_name,
            "params": params,
            "author": self.author,
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }
        return method_details

    def generate_uuid(self, method_details):
        method_details_str = json.dumps(method_details, sort_keys=True)
        return str(uuid.uuid5(uuid.UUID(self.master_token), method_details_str))

    async def set_default_for_types(self, default_value, param_type_name):
        # if the type is bool and the default value is None, set it to False
        if param_type_name == "bool" and default_value is None:
            default_value = False
        if param_type_name == "int" and default_value is None:
            default_value = 0
        if param_type_name == "float" and default_value is None:
            default_value = 0.0
        if param_type_name == "str" and default_value is None:
            default_value = ""
        return default_value

    async def register_method(self, method):
        if self.master_token is None:
            raise Exception(
                "Master Token not set. Please call set_token(token) before registering a method."
            )

        if not asyncio.iscoroutinefunction(method):
            raise ValueError("The method must be asynchronous (async).")

        method_name = method.__name__
        params = await self.validate_and_process_parameters(method)
        method_details = self.create_json_payload(method_name, params)
        self.method_details[method_name] = method_details
        self.method_registry = {method_name: method}

        #TODO: there should be a better way to do this:
        self.dawnet_token = self.generate_uuid(
            str(method_details) + str(self.master_token) + str(self.name) + str(self.version) + str(self.author) + str(
                self.description))

        await self.connect()  # Ensure we're connected

        self.dn_tracer.log_event(
            self.dawnet_token,
            {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_REG_METHOD.value,
                DNTag.DNMsg.value: f"Registered method: {method_name}",
            },
        )

    async def run_method(self, name, **kwargs):
        run_status.status = "running"
        if name in self.method_registry:
            method = self.method_registry[name]
            if asyncio.iscoroutinefunction(method):
                print("IS COROUTINE")
                # If the method is a coroutine, await it directly
                try:
                    # Capture stdout and stderr
                    stdout_buffer = io.StringIO()
                    stderr_buffer = io.StringIO()
                    sys.stdout = stdout_buffer
                    sys.stderr = stderr_buffer

                    await method(**kwargs)

                    # Restore the original stdout and stderr
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__

                    # Get the captured output as strings
                    stdout_output = stdout_buffer.getvalue()
                    stderr_output = stderr_buffer.getvalue()

                    # Now you can do whatever you want with the output
                    print("Captured stdout:")
                    print(stdout_output)
                    print("Captured stderr:")
                    print(stderr_output)

                    await self.results.add_log(stdout_output)
                    await self.results.add_log(stderr_output)

                    # If you want to save the output to a file, you can do so here
                    # with open("stdout.log", "w") as stdout_file:
                    #     stdout_file.write(stdout_output)
                    #
                    # with open("stderr.log", "w") as stderr_file:
                    #     stderr_file.write(stderr_output)

                    # if self.results.errors is None:
                    #     self.results.add_error("ENCOUNTERED AN ERROR")

                    print("ERRORS: " + str(self.results.errors))

                    await self.results.send()

                    self.dn_tracer.log_event(
                        self.dawnet_token,
                        {
                            DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                            DNTag.DNMsg.value: f"Ran method: {name}",
                        },
                    )
                except Exception as e:
                    await self.results.add_error("ERROR:" + str(e))
                    print("IM IN THE EXCEPTION")
                    await self.results.send()

                    self.dn_tracer.log_error(
                        self.dawnet_token,
                        {
                            DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                            DNTag.DNMsg.value: f"Error running method: {e}",
                        },
                    )
            else:
                print("IS NOT COROUTINE")
                # If the method is not a coroutine, run it in an executor
                # loop = asyncio.get_running_loop()
                # try:
                #     func = lambda: method(**kwargs)
                #     result = await loop.run_in_executor(None, func)
                #     self.dn_tracer.log_event(self.dawnet_token, {
                #         DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                #         DNTag.DNMsg.value: f"Ran method: {name}",
                #     })
                # except Exception as e:
                #     self.dn_tracer.log_error(self.dawnet_token, {
                #         DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                #         DNTag.DNMsg.value: f"Error running method: {e}",
                #     })

            run_status.status = "stopped"
            return True
        else:
            run_status.status = "stopped"
            raise Exception("Method not registered")

    async def download_gcp_files(self, obj, session):
        """
        Recursively search for GCP URLs in a JSON object and download the files.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith(
                        "https://storage.googleapis.com"
                ):
                    # Download and replace the URL with a local file path
                    try:
                        obj[key] = await self.download_file(value, session)

                        self.dn_tracer.log_event(
                            self.dawnet_token,
                            {
                                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_DOWNLOAD_ASSET.value,
                                DNTag.DNMsg.value: f"Downloaded: {str(obj[key])}",
                            },
                        )
                    except Exception as e:
                        self.dn_tracer.log_error(
                            self.dawnet_token,
                            {
                                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_DOWNLOAD_ASSET.value,
                                DNTag.DNMsg.value: f"Error downloading: {e}",
                            },
                        )
                elif isinstance(value, (dict, list)):
                    await self.download_gcp_files(value, session)
        elif isinstance(obj, list):
            for item in obj:
                await self.download_gcp_files(item, session)

    async def download_file(self, url, session):
        """
        Download a file from a URL, save it to a temporary directory, and process if it's an audio file.
        """
        local_filename = url.split("/")[-1]
        local_path = os.path.join(self.temp_dir, local_filename)

        async with session.get(url) as response:
            if response.status == 200:
                with open(local_path, "wb") as f:
                    f.write(await response.read())

                # Check if the file is an audio file
                if os.path.splitext(local_path)[1][1:] in [
                    "wav",
                    "mp3",
                    "aif",
                    "aiff",
                    "flac",
                    "ogg",
                ]:
                    try:
                        local_path = process_audio_file(
                            local_path,
                            self.input_format,
                            self.input_sample_rate,
                            self.input_bit_depth,
                            self.input_channels,
                        )

                        self.dn_tracer.log_event(
                            self.dawnet_token,
                            {
                                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONVERT_DOWNLOAD.value,
                                DNTag.DNMsg.value: f"Converted download: {local_path}",
                            },
                        )
                    except Exception as e:
                        self.dn_tracer.log_error(
                            self.dawnet_token,
                            {
                                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONVERT_DOWNLOAD.value,
                                DNTag.DNMsg.value: f"Error converting downloading: {e}",
                            },
                        )

                return local_path
            else:
                raise Exception(f"Failed to download file: {url}")

    async def listen(self):
        if self.dawnet_token is None:
            raise Exception(
                "Token not set. Please call set_token(token) before starting to listen."
            )

        await self.connect()  # Ensure we're connected

        try:
            # Create a temporary directory
            self.temp_dir = tempfile.mkdtemp()
            self.logger.info(f"Created a temporary directory: {self.temp_dir}")

            async with aiohttp.ClientSession() as session:
                # Continuous listening loop
                while True:
                    register_compute_instance_msg = await self.websocket.recv()

                    msg = json.loads(register_compute_instance_msg)

                    # Download GCP-hosted files and update the JSON
                    try:
                        await self.download_gcp_files(msg, session)
                    except Exception as e:
                        self.dn_tracer.log_error(
                            _client.dawnet_token,
                            {
                                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_DOWNLOAD_ASSET.value,
                                DNTag.DNMsg.value: f"Error downloading GCP files: {e}",
                            },
                        )

                    if 'type' in msg:
                        if msg["type"] == "run_method":
                            # Check if the status is already "running"
                            if run_status.status == "running":
                                await self.websocket.send("Plugin already started!")
                            else:
                                self.results.clear_outputs()  # Clear previous outputs before running the method
                                self.message_id = msg["message_id"]
                                self.results.set_message_id(self.message_id)
                                self.daw_bpm = msg["bpm"]
                                self.daw_sample_rate = msg["sample_rate"]

                                data = msg["data"]
                                method_name = data["method_name"]
                                # Extract 'value' for each parameter to build kwargs
                                params = {
                                    param_name: param_details["value"]
                                    for param_name, param_details in data["params"].items()
                                }

                                # Now you can call run_method using argument unpacking
                                asyncio.create_task(self.run_method(method_name, **params))
                        elif msg['type'] == 'close_connection':
                            try:
                                await self.websocket.close()
                            except Exception as e:
                                print("Error closing connection: ", e)

                            print("Connection closed by server")
                            break  # Exit the while loop

                    else:
                        self.dn_tracer.log_error(
                            _client.dawnet_token,
                            {
                                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                                DNTag.DNMsg.value: "UNKNOWN MESSAGE TYPE",
                            },
                        )

        except websockets.exceptions.ConnectionClosedOK:
            self.dn_tracer.log_error(
                _client.dawnet_token,
                {
                    DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                    DNTag.DNMsg.value: "Connection was closed.",
                },
            )

    def set_token(self, token):
        dn_client_token = os.getenv("DN_CLIENT_TOKEN")
        if dn_client_token:
            print("Token update is disabled because DN_CLIENT_TOKEN is set.")
            return  # Exit the function to prevent overriding the token
        self.master_token = token

    def set_author(self, author):
        self.author = author
        self.update_all_method_details()

    def set_name(self, name):
        self.name = name
        self.update_all_method_details()

    def set_description(self, description):
        self.description = description
        self.update_all_method_details()

    def set_version(self, version):
        self.version = version
        self.update_all_method_details()

    def update_all_method_details(self):
        for method_name, method_detail in self.method_details.items():
            # If method_detail is already a dict, no need to load it
            method_detail["author"] = self.author
            method_detail["name"] = self.name
            method_detail["description"] = self.description
            method_detail["version"] = self.version
            self.method_details[method_name] = method_detail  # If you need it as a dict
            # If you need to store it as a JSON string, then use json.dumps
            # self.method_details[method_name] = json.dumps(method_detail)

    def run(self):
        asyncio.run(self.listen())


# Create a single WebSocketClient instance
_client = WebSocketClient(SOCKET_IP, SOCKET_PORT)


def output():
    return _client.results


# Define the functions that will interact with the WebSocketClient instance
def set_token(token):
    # Check if DN_CLIENT_TOKEN environment variable is set and non-empty
    dn_client_token = os.getenv("DN_CLIENT_TOKEN")
    if dn_client_token:
        print("Token update is disabled because the DN_CLIENT_TOKEN env var is set.")
        return  # Exit the function to prevent overriding the token

    try:
        # Create a UUID object from the token
        uuid_obj = uuid.UUID(token)

        # Check if the formatted string of the UUID object matches the input token
        # This comparison is case-insensitive and ignores hyphens
        if uuid_obj.hex != token.replace("-", "").lower():
            raise ValueError
    except ValueError:
        raise ValueError(f"Invalid token: '{token}'. Token must be a valid UUID.")

    _client.set_token(token)



async def _register_method(method):
    await _client.register_method(method)


def register_method(method):
    try:
        asyncio.run(_register_method(method))
    except Exception as e:
        dn_tracer = SentryEventLogger(service_name=DNSystemType.DN_CLIENT.value)
        dn_tracer.log_error(
            _client.dawnet_token,
            {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_REG_METHOD.value,
                DNTag.DNMsg.value: f"Error registering method: {e}",
            },
        )


def set_author(author: str):
    _client.set_author(author)


def set_name(name: str):
    _client.set_name(name)


def set_description(description: str):
    _client.set_description(description)


def set_version(version):
    _client.set_version(version)


def set_input_target_sample_rate(sample_rate: int):
    # List of valid sample rates
    valid_sample_rates = [22050, 32000, 44100, 48000]

    # Check if the sample rate is valid
    if sample_rate in valid_sample_rates:
        _client.input_sample_rate = sample_rate
    else:
        # Raise an error if the sample rate is not valid
        raise ValueError(
            f"Invalid sample rate: '{sample_rate}'. Valid sample rates are: {', '.join(map(str, valid_sample_rates))}"
        )


def set_input_target_bit_depth(bit_depth: int):
    # List of valid bit depths
    valid_bit_depths = [16, 24]

    # Check if the bit depth is valid
    if bit_depth in valid_bit_depths:
        _client.input_bit_depth = bit_depth
    else:
        # Raise an error if the bit depth is not valid
        raise ValueError(
            f"Invalid bit depth: '{bit_depth}'. Valid bit depths are: {', '.join(map(str, valid_bit_depths))}"
        )


def set_input_target_channels(channels: int):
    # List of valid channel counts
    valid_channels = [1, 2]

    # Check if the channel count is valid
    if channels in valid_channels:
        _client.input_channels = channels
    else:
        # Raise an error if the channel count is not valid
        raise ValueError(
            f"Invalid channel count: '{channels}'. Valid channel counts are: {', '.join(map(str, valid_channels))}"
        )


def set_input_target_format(format: str):
    # List of valid formats (in lower case)
    valid_formats = ["wav", "mp3", "aif", "aiff", "flac"]

    # Convert the input format to lower case
    format_lower = format.lower()

    # Check if the format is in the list of valid formats
    if format_lower in valid_formats:
        _client.input_format = format_lower
    else:
        # Raise an error if the format is not valid
        raise ValueError(
            f"Invalid format: '{format}'. Valid formats are: {', '.join(valid_formats)}"
        )


def set_output_target_sample_rate(sample_rate: int):
    # Assuming the same valid sample rates as for input
    valid_sample_rates = [22050, 32000, 44100, 48000]
    if sample_rate in valid_sample_rates:
        _client.output_sample_rate = sample_rate
    else:
        raise ValueError(
            f"Invalid output sample rate: '{sample_rate}'. Valid rates: {valid_sample_rates}"
        )


def set_output_target_bit_depth(bit_depth: int):
    # Assuming the same valid bit depths as for input
    valid_bit_depths = [16, 24]
    if bit_depth in valid_bit_depths:
        _client.output_bit_depth = bit_depth
    else:
        raise ValueError(
            f"Invalid output bit depth: '{bit_depth}'. Valid depths: {valid_bit_depths}"
        )


def set_output_target_channels(channels: int):
    # Assuming the same valid channel counts as for input
    valid_channels = [1, 2]
    if channels in valid_channels:
        _client.output_channels = channels
    else:
        raise ValueError(
            f"Invalid output channel count: '{channels}'. Valid counts: {valid_channels}"
        )


def set_output_target_format(format: str):
    # Assuming the same valid formats as for input
    valid_formats = ["wav", "mp3", "aif", "aiff", "flac"]
    format_lower = format.lower()
    if format_lower in valid_formats:
        _client.output_format = format
    else:
        raise ValueError(
            f"Invalid output format: '{format}'. Valid formats: {valid_formats}"
        )


def get_daw_bpm():
    return _client.daw_bpm


def get_daw_sample_rate():
    return _client.daw_sample_rate


def connect_to_server():
    asyncio.run(_client.send_registered_methods_to_server())
    asyncio.run(_client.listen())


# THIS IS A SPECIAL TYPE THAT WILL BE USED TO REPRESENT FILE UPLOADS
class DAWNetFilePath(str):
    pass

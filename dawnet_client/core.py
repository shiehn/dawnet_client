import asyncio
import websockets
import nest_asyncio
import json
import logging
import os
import tempfile
import aiohttp
from dawnet_client.results_handler import ResultsHandler
from dawnet_client.config import SOCKET_IP, SOCKET_PORT
from dawnet_client.dn_tracer import SentryEventLogger, DNSystemType,DNTag, DNMsgStage
from inspect import signature, Parameter

# Apply nest_asyncio to allow nested running of event loops
nest_asyncio.apply()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RunStatus:
    def __init__(self):
        self.status = 'idle'


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
        self.run_status = 'idle'
        self.dawnet_token = None
        self.message_id = None
        self.results = None
        self.author = "Default Author"
        self.name = "Default Name"
        self.description = "Default Description"
        self.version = "0.0.0"
        self.logger = logging.getLogger(__name__)
        self.dn_tracer = SentryEventLogger(service_name=DNSystemType.DN_CLIENT.value)

    async def send_registered_methods_to_server(self):
        await self.connect()  # Ensure we're connected

        # Check if there's at least one method registered
        if self.method_registry:
            # Get the last registered method's name and details
            last_method_name, last_method = next(reversed(self.method_registry.items()))
            last_method_details = self.method_details[last_method_name]

            # Construct the message to register the method
            register_compute_contract_msg = {
                'token': self.dawnet_token,
                'type': 'contract',
                'data': last_method_details
            }

            # Send the registration message to the server
            await self.websocket.send(json.dumps(register_compute_contract_msg))
            self.dn_tracer.log_event(self.dawnet_token, {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_REG_CONTRACT.value,
                DNTag.DNMsg.value: f"Sent contract for registration. Token: {self.dawnet_token}",
            })

    async def connect(self):
        if self.websocket is None or self.websocket.closed:
            uri = f"ws://{self.server_ip}:{self.server_port}"
            self.websocket = await websockets.connect(uri)
            self.dn_tracer.log_event(self.dawnet_token, {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                DNTag.DNMsg.value: f"Connected to {uri}",
            })
            self.results = ResultsHandler(self.websocket, self.dawnet_token)

        try:
            await self.register_compute_instance()
        except Exception as e:
            self.dn_tracer.log_error(self.dawnet_token, {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                DNTag.DNMsg.value: f"Error connecting. {e}",
            })

    async def register_compute_instance(self):
        if self.dawnet_token is None:
            raise Exception("Token not set. Please call set_token(token) before registering a method.")

        # Construct the message to register the compute instance
        register_compute_instance_msg = {
            'token': self.dawnet_token,
            'type': 'register',
            'data': {
                'status': 1  # Assuming 'status': 1 indicates a successful registration
            }
        }

        # Send the registration message to the server
        await self.websocket.send(json.dumps(register_compute_instance_msg))

    async def register_method(self, name: str, method):
        if self.dawnet_token is None:
            raise Exception("Token not set. Please call set_token(token) before registering a method.")

        if not asyncio.iscoroutinefunction(method):
            raise ValueError("The method must be asynchronous (async).")

        await self.connect()  # Ensure we're connected

        sig = signature(method)
        params = []
        param_names = set()
        supported_types = {'int', 'float', 'str', 'DAWNetFilePath'}
        max_param_count = 12
        max_param_name_length = 36

        if len(sig.parameters) > max_param_count:
            raise ValueError("Method cannot have more than 12 parameters.")

        for param in sig.parameters.values():
            if len(param.name) > max_param_name_length:
                raise ValueError(f"Parameter name '{param.name}' exceeds 36 characters.")

            if param.name in param_names:
                raise ValueError(f"Duplicate parameter name '{param.name}' detected.")
            param_names.add(param.name)

            if param.annotation is Parameter.empty:
                raise ValueError(f"Parameter '{param.name}' is missing a type annotation.")

            param_type_name = param.annotation.__name__
            if param_type_name not in supported_types:
                raise ValueError(f"Unsupported type '{param_type_name}' for parameter '{param.name}'.")

            params.append({"name": param.name, "type": param_type_name, "default_value": None})

            # Create the JSON payload
            # Store method details without sending to the server
            method_details = {
                "method_name": name,
                "params": params,
                "author": self.author,
                "name": self.name,
                "description": self.description,
                "version": self.version
            }
            self.method_details[name] = method_details

            # Update registry with the latest method
            self.method_registry = {name: method}

            self.dn_tracer.log_event(self.dawnet_token, {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_REG_METHOD.value,
                DNTag.DNMsg.value: f"Registered method: {name}",
            })

    async def run_method(self, name, **kwargs):
        run_status.status = 'running'
        if name in self.method_registry:
            method = self.method_registry[name]
            if asyncio.iscoroutinefunction(method):
                # If the method is a coroutine, await it directly
                try:
                    result = await method(**kwargs)
                    self.dn_tracer.log_event(self.dawnet_token, {
                        DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                        DNTag.DNMsg.value: f"Ran method: {name}",
                    })
                except Exception as e:
                    self.dn_tracer.log_error(self.dawnet_token, {
                        DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                        DNTag.DNMsg.value: f"Error running method: {e}",
                    })
            else:
                # If the method is not a coroutine, run it in an executor
                loop = asyncio.get_running_loop()
                try:
                    func = lambda: method(**kwargs)
                    result = await loop.run_in_executor(None, func)
                    self.dn_tracer.log_event(self.dawnet_token, {
                        DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                        DNTag.DNMsg.value: f"Ran method: {name}",
                    })
                except Exception as e:
                    self.dn_tracer.log_error(self.dawnet_token, {
                        DNTag.DNMsgStage.value: DNMsgStage.CLIENT_RUN_METHOD.value,
                        DNTag.DNMsg.value: f"Error running method: {e}",
                    })
            run_status.status = 'stopped'
            return result
        else:
            run_status.status = 'stopped'
            raise Exception("Method not registered")

    async def download_gcp_files(self, obj, session):
        """
        Recursively search for GCP URLs in a JSON object and download the files.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("https://storage.googleapis.com"):
                    # Download and replace the URL with a local file path
                    obj[key] = await self.download_file(value, session)
                elif isinstance(value, (dict, list)):
                    await self.download_gcp_files(value, session)
        elif isinstance(obj, list):
            for item in obj:
                await self.download_gcp_files(item, session)

    async def download_file(self, url, session):
        """
        Download a file from a URL and save it to a temporary directory.
        """
        local_filename = url.split('/')[-1]
        local_path = os.path.join(self.temp_dir, local_filename)
        async with session.get(url) as response:
            if response.status == 200:
                with open(local_path, 'wb') as f:
                    f.write(await response.read())
                return local_path
            else:
                raise Exception(f"Failed to download file: {url}")

    async def listen(self):
        if self.dawnet_token is None:
            raise Exception("Token not set. Please call set_token(token) before starting to listen.")

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
                        self.dn_tracer.log_error(_client.dawnet_token, {
                            DNTag.DNMsgStage.value: DNMsgStage.CLIENT_DOWNLOAD_ASSET.value,
                            DNTag.DNMsg.value: f"Error downloading GCP files: {e}",
                        })

                    if msg['type'] == "run_method":
                        # Check if the status is already "running"
                        if run_status.status == "running":
                            await self.websocket.send("Plugin already started!")
                        else:
                            self.message_id = msg['message_id']
                            self.results.set_message_id(self.message_id)
                            data = msg['data']
                            method_name = data['method_name']
                            # Extract 'value' for each parameter to build kwargs
                            params = {param_name: param_details['value'] for param_name, param_details in
                                      data['params'].items()}

                            # Now you can call run_method using argument unpacking
                            asyncio.create_task(self.run_method(method_name, **params))

        except websockets.exceptions.ConnectionClosedOK:
            self.dn_tracer.log_error(_client.dawnet_token, {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONNECTION.value,
                DNTag.DNMsg.value: f"Connection was closed.",
            })

    def set_token(self, token):
        self.dawnet_token = token
        if self.results is not None:
            self.results.update_token(token)

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


def results():
    return _client.results


# Define the functions that will interact with the WebSocketClient instance
def set_token(token):
    _client.set_token(token)


async def _register_method(name, method):
    await _client.register_method(name, method)


def register_method(name, method):
    try:
        asyncio.run(_register_method(name, method))
    except Exception as e:
        dn_tracer = SentryEventLogger(service_name=DNSystemType.DN_CLIENT.value)
        dn_tracer.log_error(_client.dawnet_token, {
            DNTag.DNMsgStage.value: DNMsgStage.CLIENT_REG_METHOD.value,
            DNTag.DNMsg.value: f"Error registering method: {e}",
        })


def set_author(author):
    _client.set_author(author)


def set_name(name):
    _client.set_name(name)


def set_description(description):
    _client.set_description(description)


def set_version(version):
    _client.set_version(version)


def connect_to_server():
    asyncio.run(_client.send_registered_methods_to_server())
    asyncio.run(_client.listen())


# THIS IS A SPECIAL TYPE THAT WILL BE USED TO REPRESENT FILE UPLOADS
class DAWNetFilePath(str):
    pass

import json
import os
import tempfile

import aiohttp
from byoac.results_handler import ResultsHandler

byoc_server_ip = '0.0.0.0'
byoc_server_port = '8765'

import asyncio
import websockets
import nest_asyncio
import time
import json
from inspect import signature, Parameter

# Apply nest_asyncio to allow nested running of event loops
nest_asyncio.apply()

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
        self.byoc_token = None
        self.message_id = None
        self.results = None


    async def connect(self):
        if self.websocket is None or self.websocket.closed:
            uri = f"ws://{self.server_ip}:{self.server_port}"
            self.websocket = await websockets.connect(uri)
            print(f"Connected to {uri}")
            self.results = ResultsHandler(self.websocket, self.byoc_token)
            await self.register_compute_instance()

    async def register_compute_instance(self):
        if self.byoc_token is None:
            raise Exception("Token not set. Please call set_token(token) before registering a method.")

        # Construct the message to register the compute instance
        register_compute_instance_msg = {
            'token': self.byoc_token,
            'type': 'register',
            'data': {
                'status': 1  # Assuming 'status': 1 indicates a successful registration
            }
        }

        # Send the registration message to the server
        await self.websocket.send(json.dumps(register_compute_instance_msg))
        print("Compute instance registered with the server.")

    async def register_method(self, name, method):
        if self.byoc_token is None:
            raise Exception("Token not set. Please call set_token(token) before registering a method.")

        await self.connect()  # Ensure we're connected

        # Register the method
        self.method_registry[name] = method

        # Get the signature of the method
        sig = signature(method)

        # Build a list of dictionaries for each parameter
        params = [
            {"name": param.name, "type": param.annotation.__name__, "default_value": None}
            for param in sig.parameters.values()
            if param.annotation is not Parameter.empty
        ]

        # Create the JSON payload
        method_details = {
            "method_name": name,
            "params": params
        }
        self.method_details[name] = json.dumps(method_details)

        # Register the compute contract with the server
        register_compute_contract_msg = {
            'token': self.byoc_token,
            'type': 'contract',
            'data': method_details
        }

        await self.websocket.send(json.dumps(register_compute_contract_msg))
        print(f"Sent contract for method {name}")

    async def run_method(self, name, **kwargs):
        print('self.method_registry: ' + str(self.method_registry))

        run_status.status = 'running'
        if name in self.method_registry:
            method = self.method_registry[name]
            if asyncio.iscoroutinefunction(method):
                print("IS A COROUTINE")
                # If the method is a coroutine, await it directly
                try:
                    result = await method(**kwargs)
                    print("METHOD RESULT: " + str(result))
                except Exception as e:
                    print(f"Error running method: {e}")
            else:
                print("IS NOT A COROUTINE")
                # If the method is not a coroutine, run it in an executor
                loop = asyncio.get_running_loop()
                print("HEY")
                try:
                    print('kwargs: ' + str(kwargs))
                    # print('args: ' + str(args))

                    func = lambda: method(**kwargs)
                    result = await loop.run_in_executor(None, func)
                    print("METHOD RESULT: " + str(result))
                except Exception as e:
                    print(f"Error running method: {e}")
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
        if self.byoc_token is None:
            raise Exception("Token not set. Please call set_token(token) before starting to listen.")

        await self.connect()  # Ensure we're connected

        try:
            # Create a temporary directory
            self.temp_dir = tempfile.mkdtemp()
            print('TEMP_DIR: ' + str(self.temp_dir))

            async with aiohttp.ClientSession() as session:
                # Continuous listening loop
                while True:
                    register_compute_instance_msg = await self.websocket.recv()
                    print(f"RAW_MSG: {register_compute_instance_msg}")

                    print("PARSED_TYPE: " + str(json.loads(register_compute_instance_msg)['type']))

                    msg = json.loads(register_compute_instance_msg)

                    # Download GCP-hosted files and update the JSON
                    await self.download_gcp_files(msg, session)

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
                            params = {param_name: param_details['value'] for param_name, param_details in data['params'].items()}

                            print("PARAMS: " + str(params))


                            # Now you can call run_method using argument unpacking
                            asyncio.create_task(self.run_method(method_name, **params))

        except websockets.exceptions.ConnectionClosedOK:
            print("Connection was closed normally.")

    def set_token(self, token):
        self.byoc_token = token

    def run(self):
        asyncio.run(self.listen())


# Create a single WebSocketClient instance
_client = WebSocketClient('0.0.0.0', '8765')

def results():
    return _client.results

# Define the functions that will interact with the WebSocketClient instance
def set_token(token):
    _client.set_token(token)

async def _register_method(name, method):
    await _client.register_method(name, method)

def register_method(name, method):
    asyncio.run(_register_method(name, method))

def connect_to_server():
    _client.run()


# THIS IS A SPECIAL TYPE THAT WILL BE USED TO REPRESENT FILE UPLOADS
class ByoacFilePath(str):
    pass
import json

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

    async def listen(self):
        if self.byoc_token is None:
            raise Exception("Token not set. Please call set_token(token) before starting to listen.")

        await self.connect()  # Ensure we're connected

        try:
            # Continuous listening loop
            while True:
                register_compute_instance_msg = await self.websocket.recv()
                print(f"RAW_MSG: {register_compute_instance_msg}")

                '''
                register_compute_instance_msg = {"data": {"id": "bd7be782-b04b-4e7a-af5f-535f440511e0", "data": {"method": "run", "params": [{"name": "param_1", "type": "string", "default_value": "Hello World"}]}, "created_at": "2023-11-06T19:34:37.784584Z", "updated_at": "2023-11-06T19:34:37.784594Z"}, "type": "run_method", "token": "bd7be782-b04b-4e7a-af5f-535f440511e0"}
                '''

                print("PARSED_TYPE: " + str(json.loads(register_compute_instance_msg)['type']))

                msg = json.loads(register_compute_instance_msg)

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
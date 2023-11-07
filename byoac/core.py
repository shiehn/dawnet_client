import json

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
byoc_token = ''


# Method registry for the client
method_registry_local = {}
method_details_local = {}

async def register_method(name, method):
    # Register the method as before
    method_registry_local[name] = method

    # Get the signature of the method
    sig = signature(method)

    # Build a dictionary of parameter names and their types
    params = {param.name: param.annotation.__name__ for param in sig.parameters.values() if param.annotation is not Parameter.empty}

    # Create the JSON payload
    method_details = {
        "method_name": name,
        "params": params
    }
    method_details_local[name] = json.dumps(method_details)

    '''
    register the compute contract with the server
    '''

    register_compute_contract_msg = {
        'token': byoc_token,
        'type': 'contract',
        'data': method_details_local[name]
    }
    uri = "ws://" + str(byoc_server_ip) + ":" + str(byoc_server_port)
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(register_compute_contract_msg))


# async def start_plugin(websocket):
#     run_status.status = 'running'
#     await websocket.send(run_status.status)
#     await asyncio.sleep(10)
#     run_status.status = 'stopped'
#     await websocket.send(run_status.status)

def run_method(name, *args, **kwargs):
    run_status.status = 'running'
    if name in method_registry_local:
        run_status.status = 'stopped'
        return method_registry_local[name](*args, **kwargs)
    else:
        run_status.status = 'stopped'
        raise Exception("Method not registered")

# Define the arbitrary_method
# def arbitrary_method(a: int, b: str):
#     return f"Received an int: {a} and a string: {b}"

# Register the arbitrary_method
#register_method("arbitrary_method", arbitrary_method)

# Print the JSON payload
#print(method_details_local["arbitrary_method"])

# Now to programatically call the arbitrary_method with kwargs
#result = run_method("arbitrary_method", a=10, b="example")

#print(result)  # This should output: "Received an int: 10 and a string: example"

async def _connect_to_server_async(token):

    global byoc_token
    byoc_token = token

    uri = "ws://" + str(byoc_server_ip) + ":" + str(byoc_server_port)
    async with websockets.connect(uri) as websocket:

        '''
        First, register the compute instance with the server
        '''

        register_compute_instance_msg = {
            'token': byoc_token,
            'type': 'register',
            'data': {
                'status': 1
            }
        }

        print('REGISTER: ' +  str(register_compute_instance_msg))
        await websocket.send(json.dumps(register_compute_instance_msg))


        '''
        Third, start the loop to listen for messages etc
        '''

        try:
            # Continuous Listening loop
            while True:
                register_compute_instance_msg = await websocket.recv()
                print(f"Received: {register_compute_instance_msg}")

                '''
                register_compute_instance_msg = {"data": {"id": "bd7be782-b04b-4e7a-af5f-535f440511e0", "data": {"method": "run", "params": [{"name": "param_1", "type": "string", "default_value": "Hello World"}]}, "created_at": "2023-11-06T19:34:37.784584Z", "updated_at": "2023-11-06T19:34:37.784594Z"}, "type": "run_method", "token": "bd7be782-b04b-4e7a-af5f-535f440511e0"}
                '''

                print("PARSED_TYPE: " + str(json.loads(register_compute_instance_msg)['type']))

                msg = json.loads(register_compute_instance_msg)

                if msg['type'] == "run_method":
                    # Check if the status is already "running"
                    if run_status.status == "running":
                        await websocket.send("Plugin already started!")
                    else:
                        data = msg['data']
                        method_name = data['method_name']
                        params = {param: details['value'] for param, details in data['params'].items()}

                        # Now you can call run_method using argument unpacking
                        # run_method is assumed to be defined elsewhere and available here
                        asyncio.create_task(run_method(method_name, **params))
        except websockets.exceptions.ConnectionClosedOK:
            print("Connection was closed normally.")

def connect_to_server(token):
    asyncio.run(_connect_to_server_async(token))
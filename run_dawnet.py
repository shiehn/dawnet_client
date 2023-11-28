import argparse
import time
parser = argparse.ArgumentParser(description='Connect to DAWNet server.')
parser.add_argument('token', help='Token for DAWNet server connection')
args = parser.parse_args()

import dawnet_client
from dawnet_client import DAWNetFilePath
async def arbitrary_method(a: int, b: DAWNetFilePath):
    try:

        print(f"Input A: {a}")
        print(f"Input B: {b}")
        # print(f"Input C: {c}")
        # print(f"Input D: {d}")

        # DO INFERENCE SHIT HERE

        await dawnet_client.results().add_file(b, "wav")
        # await dawnet_client.results().add_file(c, "wav")
        await dawnet_client.results().add_message("This is a message XYZ")
        await dawnet_client.results().send()

        return True
    except Exception as e:
        print(f"Error in arbitrary_method: {e}")
        return f"Method encountered an error: {e}"


dawnet_client.set_token(token=args.token)
dawnet_client.register_method("arbitrary_method", arbitrary_method)
print("REGISTERED TOKEN & " + str("arbitrary_method"))
dawnet_client.connect_to_server()









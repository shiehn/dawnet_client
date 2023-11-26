import argparse
import time
parser = argparse.ArgumentParser(description='Connect to BYOAC server.')
parser.add_argument('token', help='Token for BYOAC server connection')
args = parser.parse_args()

import byoac
from byoac import ByoacFilePath
async def arbitrary_method(a: int, b: str, c:ByoacFilePath):
    try:

        print(f"Input A: {a}")
        print(f"Input B: {b}")
        print(f"Input C: {c}")

        # DO INFERENCE SHIT HERE

        # await byoac.results().add_file("/Users/stevehiehn/Downloads/2a11c14f-6710-4717-94ab-bd39773861d6.wav", "wav")
        # await byoac.results().add_file("/Users/stevehiehn/Downloads/75e244d9-b8eb-4ebb-a719-855689c20cca.wav", "wav")
        await byoac.results().add_file("/Users/stevehiehn/Downloads/12497c94-01d2-47cd-aac4-a0ffc7dc559c.wav", "wav")
        await byoac.results().add_message("This is a message XYZ")
        await byoac.results().send()

        return True
    except Exception as e:
        print(f"Error in arbitrary_method: {e}")
        return f"Method encountered an error: {e}"


byoac.set_token(token=args.token)
byoac.register_method("arbitrary_method", arbitrary_method)
byoac.connect_to_server()









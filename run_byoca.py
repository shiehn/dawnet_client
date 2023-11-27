import argparse
import time
parser = argparse.ArgumentParser(description='Connect to BYOAC server.')
parser.add_argument('token', help='Token for BYOAC server connection')
args = parser.parse_args()

import byoac
from byoac import ByoacFilePath
async def arbitrary_method(a: int, b: ByoacFilePath, c:ByoacFilePath, d:str):
    try:

        print(f"Input A: {a}")
        print(f"Input B: {b}")
        print(f"Input C: {c}")
        print(f"Input D: {d}")

        # DO INFERENCE SHIT HERE

        await byoac.results().add_file(b, "wav")
        await byoac.results().add_file(c, "wav")
        await byoac.results().add_message("This is a message XYZ")
        await byoac.results().send()

        return True
    except Exception as e:
        print(f"Error in arbitrary_method: {e}")
        return f"Method encountered an error: {e}"


byoac.set_token(token=args.token)
byoac.register_method("arbitrary_method", arbitrary_method)
byoac.connect_to_server()









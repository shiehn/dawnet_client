import argparse
import time

import byoac

parser = argparse.ArgumentParser(description='Connect to BYOAC server.')
parser.add_argument('token', help='Token for BYOAC server connection')

args = parser.parse_args()

def arbitrary_method(a: int, b: str):
    try:
        # Simulate a longer-running operation
        time.sleep(1)
        print(f"THE METHOD RAN! Received an int: {a} and a string: {b}")
        return "Method completed successfully."
    except Exception as e:
        print(f"Error in arbitrary_method: {e}")
        return f"Method encountered an error: {e}"

byoac.set_token(token=args.token)
byoac.register_method("arbitrary_method", arbitrary_method)
byoac.connect_to_server()









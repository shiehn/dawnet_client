import argparse
import time

parser = argparse.ArgumentParser(description='Connect to DAWNet server.')
parser.add_argument('token', help='Token for DAWNet server connection')
args = parser.parse_args()

import dawnet_client.core as dawnet
from dawnet_client.core import DAWNetFilePath

async def arbitrary_method(a: int, b: DAWNetFilePath):
    try:
        print(f"Input A: {a}")
        print(f"Input B: {b}")

        # DO INFERENCE SHIT HERE

        await dawnet.results().add_file(b)
        # await dawnet.results().add_file(c)
        await dawnet.results().add_message("This is a message XYZ")
        await dawnet.results().send()

        return True
    except Exception as e:
        print(f"Error in arbitrary_method: {e}")
        return f"Method encountered an error: {e}"

dawnet.set_input_target_format('wav')
dawnet.set_input_target_channels(2)
dawnet.set_input_target_sample_rate(44100)
dawnet.set_input_target_bit_depth(16)

dawnet.set_output_target_format('wav')
dawnet.set_output_target_channels(2)
dawnet.set_output_target_sample_rate(44100)
dawnet.set_output_target_bit_depth(16)

dawnet.set_token(token=args.token)
dawnet.set_name("My Remote Code")
dawnet.set_description("This is not a real description.")
dawnet.register_method("arbitrary_method", arbitrary_method)


print("REGISTERED TOKEN & " + str(arbitrary_method))
dawnet.connect_to_server()









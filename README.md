# DAWNet

`DAWNet` is a DAW (digit audio workstation) plugin that connects to a remote Google Colab or Script.  A user can send audio files from the plugin for remote processing. Hence, perform computationally expensive tasks such as text-2-audio or stem separation without leaving the DAW. 

For more information:

- [https://dawnet.tools/](https://dawnet.tools/)

- [Community Discord](https://discord.gg/UcHCjfpRkV)

# dawnet-client

The `DAWNet client` (this repo) is a python3 pip package.  It is used to create `DAWNet remotes`.  The client is responsible for moving data and files backand forth from the plugin (and server).   The client allows a user to register python functions with the DAWNet discovery server. After a function has been registered it can then be triggered remotely from `DAWNet plugin.   

::: warning
NOTE: The plugin is in an active, pre-alpha state.  It has only been tested on Ableton 11 on MAC M1.
:::

## Installation

```python
pip install dawnet-client --upgrade
```

## Tests

from the root of the source code dir run:
```python
pip uninstall dawnet-client -y && pip install -e . && pytest -s
```

## Usage

This is a simple example of a DAWNet remote script created using the dawnet-client.  The script defines an arbitrary function that takes two arguments, an integer and a DAWNetFilePath.  The function is registered with the DAWNet discovery server.  The script then connects to the DAWNet discovery server and waits for a remote trigger. 

For thorough documentation and tutorials visit: [https://dawnet.tools/client/](https://dawnet.tools/client/)

```python
import dawnet_client.core as dawnet 
from dawnet_client import DAWNetFilePath, ui_param

# The token is generated by the DAWNet plugin.  
# It is used by the discovery server to associate the remote with the plugin.
TOKEN="0715c132-0b31-406e-b562-9206c479a48a" 

# The registered method can be named anything. Note: the method must be `async`.  
# All parameters must be type hinted.  
# 4 parameter types are supported: int, float, str, DAWNetFilePath
# DAWNetFilePath is a special type. When the file is sent to the remote, it is intercepted by the system and 
# transported to a temp dir on the remote.  In this case the variable `b` is local path to the file.

# The `ui_param` is an optional decorator. It is used to define how the parameter input UI will be rendered in the plugin.  
# If the decorator is not used, the parameter will be rendered as a text input field. 
@ui_param('a', 'DAWNetNumberSlider', min=0, max=10, step=1, default=5)
@ui_param('c', 'DAWNetMultiChoice', options=['cherries', 'oranges', 'grapes'], default='grapes')
async def arbitrary_method(a: int, b: DAWNetFilePath, c: str):
    try: 
        # -----------------------------------------
        # This is where you can write custom code to operate on the input params.
        # ex param `a` could be the number of variations created from param `b` using something like MusicLM
        # -----------------------------------------
        
        # This is how you send results back to the plugin, when processing is complete.
        await dawnet.results().add_file(b) 
        # This message is displayed in the plugin.
        await dawnet.results().add_message("This is a message XYZ") 

        return True
    except Exception as e: 
        #explicitly send an error message back to the plugin
        await dawnet.results().add_error(f"Method encountered an error: {e}")
        return False


# The token generated by the plugin. 
dawnet.set_token(token=TOKEN)
# The name of the remote.  This is displayed in the plugin.
dawnet.set_name("My Remote Code")
# The description of the remote.  This is displayed in the plugin.
dawnet.set_description("This is not a real description.")
# Register the method with the discovery server.
dawnet.register_method(arbitrary_method)

# When a file is sent to the remote as a DAWNetFilePath, it will become available at this sample rate. 
dawnet.set_input_target_sample_rate(44100) #supported values [22050, 32000, 44100, 48000]
# When a file is sent to the remote as a DAWNetFilePath, it will become available at this bit rate. 
dawnet.set_input_target_bit_depth(16) #supported values [16, 24, 32]
# When a file is sent to the remote as a DAWNetFilePath, it will become available with this number of channels.
dawnet.set_input_target_channels(2) #supported values [1, 2] mono/stereo respectively
# When a file is sent to the remote as a DAWNetFilePath, it will become available in this format.
dawnet.set_input_target_format('wav') #supported values ["wav", "mp3", "aif", "flac"]

# When results are sent back to the plugin, they will be sent at this sample rate.
dawnet.set_output_target_sample_rate(44100)
# When results are sent back to the plugin, they will be sent at this bit rate.
dawnet.set_output_target_bit_depth(16)
# When results are sent back to the plugin, they will be sent with this number of channels.
dawnet.set_output_target_channels(2)
# When results are sent back to the plugin, they will be sent in this format.
dawnet.set_output_target_format('wav')

# This should be the last line of the script.  It connects to the discovery server and waits for a remote trigger.
dawnet.connect_to_server()
```


## CONFIGURATION:

*Note:* If the following environment variables are not set, the client will use the default values.  The default values will point to the public DAWNet server.  If you wish to host your own instance you will need to configure the following environment variables. 

```
export DN_CLIENT_API_BASE_URL='http://localhost:8081'
export DN_CLIENT_SOCKET_IP='0.0.0.0'
export DN_CLIENT_SOCKET_PORT='8765'
export DN_CLIENT_SENTRY_API_KEY='XXX'
"DN_CLIENT_STORAGE_BUCKET", "https://storage.googleapis.com/your_gcp_bucket/"
```

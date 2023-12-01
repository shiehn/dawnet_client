import os

API_BASE_URL = os.getenv('DAWNET_API_BASE_URL', 'https://signalsandsorcery.ai')
SOCKET_IP = os.getenv('DAWNET_SOCKET_IP', '35.223.141.253')
SOCKET_PORT = os.getenv('DAWNET_SOCKET_PORT', '8765')
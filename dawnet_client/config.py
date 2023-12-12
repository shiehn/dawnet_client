import os


# --------- DEVELOPMENT SETTINGS ----------------
API_BASE_URL = os.getenv('DAWNET_API_BASE_URL', 'http://localhost:8000')
SOCKET_IP = os.getenv('DAWNET_SOCKET_IP', 'localhost')
SENTRY_API_KEY = "https://dbbf2855a707e0448957ad77111449c3@o4506379662131200.ingest.sentry.io/4506379670847488"

# --------- PRODUCTION SETTINGS ----------------
#SOCKET_IP = os.getenv('DAWNET_SOCKET_IP', '35.223.141.253')
#API_BASE_URL = os.getenv('DAWNET_API_BASE_URL', 'https://signalsandsorcery.ai')
#SENTRY_API_KEY = "https://dbbf2855a707e0448957ad77111449c3@o4506379662131200.ingest.sentry.io/4506379670847488"

# --------- SHARED SETTINGS ----------------
SOCKET_PORT = os.getenv('DAWNET_SOCKET_PORT', '8765')

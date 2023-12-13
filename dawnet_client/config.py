import os

# --------- PRODUCTION SETTINGS ----------------
SOCKET_IP = os.getenv('DN_CLIENT_SOCKET_IP', '35.223.141.253')
API_BASE_URL = os.getenv('DN_CLIENT_API_BASE_URL', 'https://signalsandsorcery.ai')
SENTRY_API_KEY = os.getenv('DN_CLIENT_SENTRY_API_KEY', "https://dbbf2855a707e0448957ad77111449c3@o4506379662131200.ingest.sentry.io/4506379670847488")
SOCKET_PORT = os.getenv('DN_CLIENT_SOCKET_PORT', '8765')

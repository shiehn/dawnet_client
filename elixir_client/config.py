import os

# --------- PRODUCTION SETTINGS ----------------
SOCKET_IP = os.getenv("DN_CLIENT_SOCKET_IP", "34.135.228.111")
API_BASE_URL = os.getenv("DN_CLIENT_API_BASE_URL", "http://34.135.228.111:8081")
SENTRY_API_KEY = os.getenv(
    "DN_CLIENT_SENTRY_API_KEY",
    "https://dbbf2855a707e0448957ad77111449c3@o4506379662131200.ingest.sentry.io/4506379670847488",
)
SOCKET_PORT = os.getenv("DN_CLIENT_SOCKET_PORT", "8765")
STORAGE_BUCKET_PATH = os.getenv("DN_CLIENT_STORAGE_BUCKET", "https://storage.googleapis.com/byoc-file-transfer/")

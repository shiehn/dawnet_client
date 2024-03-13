import os

from aiohttp import ClientSession
from .config import API_BASE_URL, STORAGE_BUCKET_PATH


class FileUploader:
    async def get_signed_url(self, filename, token) -> str:
        url = (
            f"{API_BASE_URL}/api/hub/get_signed_url/?token={token}&filename={filename}"
        )
        async with ClientSession() as session:
            async with session.get(url) as response:
                # TODO: Check if response is ok
                data = await response.json()
                return data["signed_url"]

    async def upload_file_to_gcp(self, file_path, signed_url, file_type) -> bool:
        async with ClientSession() as session:
            with open(file_path, "rb") as file:
                async with session.put(
                    signed_url, data=file, headers={"Content-Type": file_type}
                ) as response:
                    return response.status == 200

    async def upload(self, file_path, file_type) -> str:
        file_name = os.path.basename(file_path)
        storage_bucket_path = STORAGE_BUCKET_PATH.rstrip('/')
        file_url = f"{storage_bucket_path}/{file_name}"
        signed_url = await self.get_signed_url(file_name, "myToken")
        result = await self.upload_file_to_gcp(file_path, signed_url, file_type)

        if result:
            return file_url
        else:
            raise Exception("Failed to upload file to GCP")

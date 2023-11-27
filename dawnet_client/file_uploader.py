import os

from aiohttp import ClientSession
from dawnet_client.config import API_BASE_URL


class FileUploader:
    async def get_signed_url(self, filename, token) -> str:
        url = f"{API_BASE_URL}/api/hub/get_signed_url/?token={token}&filename={filename}"
        async with ClientSession() as session:
            async with session.get(url) as response:
                # TODO: Check if response is ok
                data = await response.json()
                return data['signed_url']


    async def upload_file_to_gcp(self, file_path, signed_url, file_type):
        async with ClientSession() as session:
            with open(file_path, 'rb') as file:
                async with session.put(signed_url, data=file, headers={'Content-Type': file_type}) as response:
                    if response.status == 200:
                        print(f'File uploaded successfully to GCP Storage: {signed_url}')
                        # Handle successful upload here
                    else:
                        print(f'File upload to GCP Storage failed. Status: {response.status}')
                        # Handle failed upload here


    async def upload(self, file_path, file_type) -> str:
        file_name = os.path.basename(file_path)
        file_url = f"https://storage.googleapis.com/byoc-file-transfer/{file_name}"
        signed_url = await self.get_signed_url(file_name, 'myToken')
        await self.upload_file_to_gcp(file_path, signed_url, file_type)
        return file_url
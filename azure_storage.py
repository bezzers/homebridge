import os
from azure.storage.blob import BlobClient

class AZ_BLOB:

    def __init__(self, azure_connection_string):
        self.connection_string = azure_connection_string

    def write(self, file, blob_name, container_name):       
        try:
            blob = BlobClient.from_connection_string(conn_str=self.connection_string, container_name=container_name, blob_name=blob_name)
            with open(file, "rb") as data:
                blob.upload_blob(data, overwrite=True)
            os.remove(file)

        except:
            if os.path.exists(file):
                os.remove(file)
            raise Exception('Failed to upload to Azure Blob Service')

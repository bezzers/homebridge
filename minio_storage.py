import os
import s3fs

class BLOB:
    def __init__(self, connection_string, container_name):
        connection_spec = dict(x.split("=") for x in connection_string.split(";"))
        self.s3 = s3fs.S3FileSystem(
            key=connection_spec['key'],
            secret=connection_spec['secret'],
            client_kwargs={
                'endpoint_url': connection_spec['endpoint']
            }
        )
        self.container_name =container_name

    def write(self, df, blob_name):       
        with self.s3.open(self.container_name + '/' + blob_name, "wb") as f:
            df.to_parquet(f)

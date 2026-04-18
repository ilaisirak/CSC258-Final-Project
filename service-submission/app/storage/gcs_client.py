from google.cloud import storage
from app.config import GCS_BUCKET

class GCSClient:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(GCS_BUCKET)

    def upload_file(self, file_name, data):
        blob = self.bucket.blob(file_name)
        blob.upload_from_string(data)
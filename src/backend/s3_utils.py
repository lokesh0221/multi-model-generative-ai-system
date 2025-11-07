import os
import uuid
import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

def s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def upload_bytes(data: bytes, key: str, content_type: str = "image/png") -> str:
    """Upload bytes to S3 and return public URL (bucket must allow public read or use presigned URL)."""
    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET not set in environment")
    client = s3_client()
    try:
        client.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    except ClientError as e:
        raise
    # Return presigned URL
    url = client.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': key}, ExpiresIn=3600)
    return url


def make_key(prefix: str = "generated", extension: str = "png") -> str:
    return f"{prefix}/{uuid.uuid4().hex}.{extension}"

import os
import boto3
import urllib.parse

s3 = boto3.client("s3")
BUCKET_NAME = os.getenv("BUCKET_NAME")

def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        raw_key = path_params.get("objectKey")

        if not raw_key:
            return error(400, "objectKey is required")

        # Decode URL-encoded S3 key (important!)
        object_key = urllib.parse.unquote(raw_key)

        presigned_url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key
            },
            ExpiresIn=3600  # 1 hour
        )

        # HTTP redirect to S3
        return {
            "statusCode": 302,
            "headers": {
                "Location": presigned_url
            }
        }

    except Exception as e:
        return error(500, str(e))

def error(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": f'{{"error":"{message}"}}'
    }

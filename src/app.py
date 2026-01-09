import json
import os
import boto3

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))

        file_name = body.get("fileName")
        content_type = body.get("contentType", "image/jpeg")

        if not file_name:
            return response(400, {"message": "fileName is required"})

        object_key = f"uploads/{file_name}"

        presigned_post = s3.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type}
            ],
            ExpiresIn=300
        )

        return response(200, {
            "url": presigned_post["url"],
            "fields": presigned_post["fields"],
            "objectKey": object_key
        })

    except Exception as e:
        return response(500, {"error": str(e)})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }

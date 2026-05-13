import boto3
from PIL import Image
import os
import uuid
import urllib.parse

# S3 client
s3 = boto3.client('s3')

# DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# DynamoDB table
table = dynamodb.Table('image-metadata')

# Destination bucket
DEST_BUCKET = 'ramneek-resized-images1'

def lambda_handler(event, context):

    print("Event received:", event)

    for record in event['Records']:

        # Source bucket
        bucket_name = record['s3']['bucket']['name']

        # Decode S3 object key correctly
        object_key = urllib.parse.unquote_plus(
            record['s3']['object']['key']
        )

        print("Processing file:", object_key)

        # Temporary file paths
        download_path = f'/tmp/{uuid.uuid4()}.jpg'
        upload_path = f'/tmp/resized-{uuid.uuid4()}.jpg'

        # Download image from S3
        s3.download_file(
            bucket_name,
            object_key,
            download_path
        )

        # Open image
        image = Image.open(download_path)

        # Resize image
        image.thumbnail((300, 300))

        # Save resized image
        image.save(upload_path)

        # Resized image name
        resized_key = f"resized-{os.path.basename(object_key)}"

        # Upload resized image to destination bucket
        s3.upload_file(
            upload_path,
            DEST_BUCKET,
            resized_key
        )

        print("Upload complete:", resized_key)

        # Store metadata in DynamoDB
        table.put_item(
            Item={
                'image_id': str(uuid.uuid4()),
                'original_image': object_key,
                'resized_image': resized_key,
                'source_bucket': bucket_name,
                'destination_bucket': DEST_BUCKET
            }
        )

        print("Metadata stored in DynamoDB")

    return {
        'statusCode': 200,
        'body': 'Image resized and metadata stored successfully'
    }
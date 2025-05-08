import boto3
from botocore.exceptions import NoCredentialsError
import os

BUCKET_NAME = "legal-doc-review"  
AWS_REGION = "us-east-1"

s3 = boto3.client('s3', region_name=AWS_REGION)

def upload_file_to_s3(file_path):
    if not os.path.isfile(file_path):
        print("❌ Invalid file path. Please check and try again.")
        return

    file_name = os.path.basename(file_path)

    try:
        s3.upload_file(file_path, BUCKET_NAME, file_name)
        print(f"✅ File uploaded successfully as '{file_name}'")
    except NoCredentialsError:
        print("❌ AWS credentials not found. Run 'aws configure'.")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    path = input("Enter the full path to your legal document: ").strip()
    upload_file_to_s3(path)

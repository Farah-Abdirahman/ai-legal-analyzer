import boto3
import time
import os
import botocore.exceptions

BUCKET_NAME = "legal-doc-review"  
AWS_REGION = "us-east-1"

s3 = boto3.client('s3', region_name=AWS_REGION)
textract = boto3.client('textract', region_name=AWS_REGION)

def check_s3_object_exists(bucket, key):
    """Check if an object exists in the S3 bucket"""
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

def extract_pdf(s3_object):
    # First check if the object exists in S3
    if not check_s3_object_exists(BUCKET_NAME, s3_object):
        print(f"❌ Error: The file '{s3_object}' does not exist in bucket '{BUCKET_NAME}'")
        return None
    
    try:
        response = textract.start_document_text_detection(
            DocumentLocation={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_object}}
        )
        job_id = response['JobId']
        print(f"✅ Job started with ID: {job_id}")

        # Let's wait for the job to complete
        while True:
            status = textract.get_document_text_detection(JobId=job_id)
            job_status = status['JobStatus']
            if job_status in ['SUCCEEDED', 'FAILED']:
                break
            print(f"⏳ Job status: {job_status}. Waiting for 5 seconds...")
            time.sleep(5)
            
        if job_status == 'FAILED':
            print("❌ Textract failed to process the document.")
            return None
            
        print("✅ Job completed successfully.")
        
        # Get all pages of results
        pages = []
        pages.append(status)
        next_token = status.get('NextToken', None)
        
        while next_token:
            status = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
            pages.append(status)
            next_token = status.get('NextToken', None)
        
        # Extract text from all pages
        extracted_text = ""
        for page in pages:
            blocks = page['Blocks']
            page_text = "\n".join([block['Text'] for block in blocks if block['BlockType'] == 'LINE'])
            extracted_text += page_text + "\n"
            
        return extracted_text
    except botocore.exceptions.ClientError as e:
        print(f"❌ AWS Error: {e}")
        return None

if __name__ == '__main__':
    s3_key = input("Enter the File Name from the bucket: ").strip()
    text = extract_pdf(s3_key)

    if text:
        with open('extracted.txt','w', encoding='utf-8') as f:
            f.write(text)
        print("✅ Text extracted and saved to extracted.txt")
    else:
        print("❌ Failed to extract text from the document.")
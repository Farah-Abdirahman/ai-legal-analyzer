import streamlit as st
import boto3
import json
import tempfile
import os
import time
from PIL import Image
import io
import re

st.set_page_config(
    page_title="Legal Contract Analyzer",
    page_icon="⚖️",
    layout="wide"
)

@st.cache_resource
def get_aws_clients():
    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
        textract = boto3.client("textract", region_name="us-east-1")
        s3 = boto3.client("s3", region_name="us-east-1")
        return bedrock, textract, s3
    except Exception as e:
        st.error(f"Error connecting to AWS services: {str(e)}")
        return None, None, None

MODEL_ID = "amazon.nova-lite-v1:0"
BUCKET_NAME = "legal-doc-review"  
def run_nova_legal_task(prompt, bedrock_client):
    system_prompt = [
        {
            "text": "You are a legal document assistant. You help lawyers summarize contracts, extract key clauses, and identify legal risks or unusual terms. Be concise and accurate. IMPORTANT: Always provide your responses in plain text format, not JSON. Use markdown formatting for headings and lists."
        }
    ]
    
    message_list = [{"role": "user", "content": [{"text": prompt + "\n\nIMPORTANT: Provide your response in plain text format, not as JSON. Use markdown formatting for structure."}]}]
    
    # Inference settings
    inf_params = {"maxTokens": 1000, "topP": 0.9, "topK": 20, "temperature": 0.3}
    
    try:
        request_body = {
            "schemaVersion": "messages-v1",
            "system": system_prompt,
            "messages": message_list,
            "inferenceConfig": inf_params
        }
        
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        result = json.loads(response["body"].read())
        

        if "message" in result and "content" in result["message"]:
            content = result["message"]["content"]
            if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                return content[0]["text"]
        elif "output" in result and "message" in result["output"]:
            if "content" in result["output"]["message"]:
                content = result["output"]["message"]["content"]
                if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                    return content[0]["text"]
        
        result_str = str(result)
        match = re.search(r"'text': '(.*?)(?:'|\")", result_str, re.DOTALL)
        if match:
            return match.group(1)
        
        return str(result)
            
    except Exception as e:
        st.error(f"Error during model invocation: {str(e)}")
        return f"Error: {str(e)}"

def clean_response(response_text):
    # Check if the response looks like a JSON object
    if response_text.strip().startswith('{') and '}' in response_text:
        try:
            # Try to extract just the text content from the JSON
            match = re.search(r"'text': '(.*?)(?:'|\")", response_text, re.DOTALL)
            if match:
                return match.group(1)
            
            # If that fails, try to parse the JSON and extract the text
            data = json.loads(response_text.replace("'", '"'))
            if "output" in data and "message" in data["output"] and "content" in data["output"]["message"]:
                content = data["output"]["message"]["content"]
                if isinstance(content, list) and len(content) > 0 and "text" in content[0]:
                    return content[0]["text"]
        except:
            pass
    
    return response_text

def upload_to_s3(file_bytes, file_name, s3_client):
   
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=file_bytes
        )
        return True
    except Exception as e:
        st.error(f"Error uploading to S3: {str(e)}")
        return False
# Here we extract text from pdf using textract
def extract_text_with_textract(file_bytes, file_name, textract_client, s3_client):
    try:
        # First we upload the file to S3
        s3_key = f"uploads/{file_name}"
        upload_success = upload_to_s3(file_bytes, s3_key, s3_client)
        
        if not upload_success:
            return "Error uploading file to S3"
        
        # Start the Textract job
        with st.spinner("Starting Textract text extraction..."):
            response = textract_client.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': BUCKET_NAME, 'Name': s3_key}}
            )
            job_id = response['JobId']
            
            # Wait for the job to complete
            status = 'IN_PROGRESS'
            while status == 'IN_PROGRESS':
                time.sleep(3)
                response = textract_client.get_document_text_detection(JobId=job_id)
                status = response['JobStatus']
                st.write(f"Textract job status: {status}")
            
            if status != 'SUCCEEDED':
                return f"Textract job failed with status: {status}"
            
            # Get all pages of results
            pages = [response]
            next_token = response.get('NextToken', None)
            
            while next_token:
                response = textract_client.get_document_text_detection(
                    JobId=job_id,
                    NextToken=next_token
                )
                pages.append(response)
                next_token = response.get('NextToken', None)
            
            # Extract text from all pages
            extracted_text = ""
            for page in pages:
                blocks = page['Blocks']
                for block in blocks:
                    if block['BlockType'] == 'LINE':
                        extracted_text += block['Text'] + "\n"
            
            return extracted_text
            
    except Exception as e:
        st.error(f"Error in Textract processing: {str(e)}")
        return f"Error extracting text: {str(e)}"

# StreamLit Frontend
st.title("⚖️ Legal Contract Analyzer")
st.markdown("""
This app analyzes legal contracts using Nova AI models. 
Upload a contract document to get a summary, key clauses, and potential risks.
""")

# Sidebar for AWS configuration
with st.sidebar:
    st.header("About")
    st.info("This tool uses Amazon Bedrock to analyze legal contracts and identify key information.")
    
    st.header("Settings")
    st.markdown("**AWS Configuration**")
    
    st.success("✅ Using configured AWS credentials")

# Main content area
tab1, tab2 = st.tabs(["Analyze Contract", "View Results"])

with tab1:
    st.header("Upload Contract")
    
    # Lets use file uploader to upload the contract document
    uploaded_file = st.file_uploader("Choose a contract document", type=["txt", "pdf", "docx"])
    
    if uploaded_file is not None:
        st.success(f"Uploaded: {uploaded_file.name}")
        
        # Get AWS clients
        bedrock_client, textract_client, s3_client = get_aws_clients()
        
        if not all([bedrock_client, textract_client, s3_client]):
            st.error("Failed to initialize AWS clients. Please check your credentials.")
        else:
            # Extract text based on file type
            if uploaded_file.type == "application/pdf":
                st.info("Processing PDF document with AWS Textract...")
                contract_text = extract_text_with_textract(
                    uploaded_file.getvalue(), 
                    uploaded_file.name, 
                    textract_client, 
                    s3_client
                )
            elif uploaded_file.type == "text/plain":
                contract_text = uploaded_file.getvalue().decode("utf-8")
            else:
                st.warning("File type not fully supported. Results may vary.")
                contract_text = uploaded_file.getvalue().decode("utf-8")
            
            # Display a preview of the text
            with st.expander("Preview Extracted Text"):
                st.text_area("Contract Text", contract_text, height=200)
            
            # Analysis options
            st.subheader("Analysis Options")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                do_summary = st.checkbox("Generate Summary", value=True)
            with col2:
                do_clauses = st.checkbox("Extract Key Clauses", value=True)
            with col3:
                do_risks = st.checkbox("Identify Risks", value=True)
            
            # Analyze button
            if st.button("Analyze Contract"):
                # Initialize session state for results if not already done
                if "results" not in st.session_state:
                    st.session_state.results = {}
                
                with st.spinner("Analyzing contract... This may take a minute."):
                    results = {}
                    
                    if do_summary:
                        st.info("Generating summary...")
                        summary_prompt = f"Summarize the following legal contract as coincise as possible in bullet points. Format your response as plain text with markdown bullet points, not as JSON:\n\n{contract_text}"
                        response = run_nova_legal_task(summary_prompt, bedrock_client)
                        results["summary"] = clean_response(response)
                    
                    if do_clauses:
                        st.info("Extracting key clauses...")
                        clauses_prompt = f"Extract all important legal clauses and their purposes from this contract. Format your response as plain text with markdown headings and bullet points, not as JSON:\n\n{contract_text}"
                        response = run_nova_legal_task(clauses_prompt, bedrock_client)
                        results["clauses"] = clean_response(response)
                    
                    if do_risks:
                        st.info("Identifying risks...")
                        risks_prompt = f"Identify any potential risks or unusual terms in this contract and explain them clearly. Format your response as plain text with markdown headings and bullet points, not as JSON:\n\n{contract_text}"
                        response = run_nova_legal_task(risks_prompt, bedrock_client)
                        results["risks"] = clean_response(response)
                    
                    # Save results to session state
                    st.session_state.results = results
                    
                    # Switch to results tab
                    st.success("Analysis complete! View the results in the 'View Results' tab.")
                    st.balloons()

with tab2:
    st.header("Analysis Results")
    
    if "results" in st.session_state and st.session_state.results:
        results = st.session_state.results
        
        if results:
            report_text = ""
            if "summary" in results:
                report_text += "📋 SUMMARY\n" + "="*50 + "\n" + results["summary"] + "\n\n"
            if "clauses" in results:
                report_text += "📑 KEY CLAUSES\n" + "="*50 + "\n" + results["clauses"] + "\n\n"
            if "risks" in results:
                report_text += "⚠️ RISKS / UNUSUAL TERMS\n" + "="*50 + "\n" + results["risks"] + "\n\n"
            
            st.download_button(
                label="Download Full Report",
                data=report_text,
                file_name="contract_analysis.txt",
                mime="text/plain"
            )
        
        if "summary" in results:
            with st.expander("📋 Summary", expanded=True):
                st.markdown(results["summary"])
        
        if "clauses" in results:
            with st.expander("📑 Key Clauses", expanded=True):
                st.markdown(results["clauses"])
        
        if "risks" in results:
            with st.expander("⚠️ Risks / Unusual Terms", expanded=True):
                st.markdown(results["risks"])
    else:
        st.info("No analysis results yet. Upload and analyze a contract to see results here.")

st.markdown("---")
st.caption("Powered by AWS Bedrock and Streamlit")

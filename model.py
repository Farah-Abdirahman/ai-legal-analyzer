import boto3
import json

client = boto3.client("bedrock-runtime", region_name="us-east-1")
LITE_MODEL_ID = "us.amazon.nova-lite-v1:0"

system_prompt = [
    {
        "text": "You are a legal document assistant. You help lawyers summarize contracts, extract key clauses, and identify legal risks or unusual terms. Be concise and accurate."
    }
]

inf_params = {"maxTokens": 1000, "topP": 0.9, "topK": 20, "temperature": 0.3}

def run_nova_legal_task(prompt):
    message_list = [{"role": "user", "content": [{"text": prompt}]}]

    request_body = {
        "schemaVersion": "messages-v1",
        "system": system_prompt,
        "messages": message_list,
        "inferenceConfig": inf_params
    }

    try:
        response = client.invoke_model(
            modelId=LITE_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        result = json.loads(response["body"].read())
        
        # Print the structure to debug
        print("Response structure:", json.dumps(result, indent=2)[:200] + "...")
        
        # Try to extract the response based on common response formats
        if "output" in result:
            output = result["output"]
        elif "content" in result:
            if isinstance(result["content"], list):
                output = result["content"][0]["text"]
            else:
                output = result["content"]
        elif "message" in result:
            output = result["message"]["content"]
        elif "completion" in result:
            output = result["completion"]
        else:
            # Return the whole result as a string if we can't find the expected fields
            output = str(result)
        
        # Ensure output is a string
        if isinstance(output, dict) or isinstance(output, list):
            return json.dumps(output, indent=2)
        return str(output)
            
    except Exception as e:
        print(f"Error during model invocation: {str(e)}")
        return f"Error: {str(e)}"


# Load contract text extracted from Textract
try:
    with open("extracted.txt", "r", encoding="utf-8") as f:
        contract_text = f.read()
    print("✅ Successfully loaded contract text")
except Exception as e:
    print(f"❌ Error loading contract text: {str(e)}")
    exit(1)

# Define prompts for each task
summary_prompt = f"Summarize the following legal contract in bullet points:\n\n{contract_text}"
clauses_prompt = f"Extract all important legal clauses and their purposes from this contract:\n\n{contract_text}"
risks_prompt = f"Identify any potential risks or unusual terms in this contract and explain them clearly:\n\n{contract_text}"

try:
    # Run all prompts
    print("Generating summary...")
    summary = run_nova_legal_task(summary_prompt)
    print("Extracting key clauses...")
    clauses = run_nova_legal_task(clauses_prompt)
    print("Identifying risks...")
    risks = run_nova_legal_task(risks_prompt)

    # Save outputs to a report file
    with open("analysis_output.txt", "w", encoding="utf-8") as f:
        f.write("📋 SUMMARY\n" + summary + "\n\n")
        f.write("📑 KEY CLAUSES\n" + clauses + "\n\n")
        f.write("⚠️ RISKS / UNUSUAL TERMS\n" + risks + "\n\n")

    print("✅ Document analysis complete. Results saved to 'analysis_output.txt'")
except Exception as e:
    print(f"❌ Error during analysis: {str(e)}")
    print("Detailed error information:")
    import traceback
    traceback.print_exc()

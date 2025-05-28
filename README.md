# Legal Document Analyzer ⚖️

This project is an AI-powered legal document analyzer designed to assist lawyers and legal professionals in summarizing contracts, extracting key clauses, and identifying potential risks or unusual terms. It leverages **Amazon Bedrock** and **Amazon Textract** to process legal documents and generate insights.

## Features

- **Summarize Contracts**: Provides concise summaries of legal documents in bullet points.
- **Extract Key Clauses**: Identifies and explains important legal clauses and their purposes.
- **Identify Risks**: Highlights potential risks or unusual terms in contracts.
- **Streamlined Workflow**: Automates the analysis process from text extraction to AI-powered insights.

## How It Works

1. **Text Extraction**: The document is processed using **Amazon Textract** to extract text.
2. **AI Analysis**: The extracted text is analyzed using **Amazon Bedrock** with the Nova model to generate summaries, extract clauses, and identify risks.
3. **Results**: The analysis results are saved to a report file for review.

## Project Structure

```
.
├── analysis_output.txt    # Output file containing analysis results
├── extracted.txt          # Extracted text from the uploaded document
├── extract_text.py        # Script for extracting text using Amazon Textract
├── frontend.py            # Streamlit-based frontend for user interaction
├── model.py               # Core logic for AI-powered analysis using Amazon Bedrock
├── s3_upload.py           # Utility for uploading files to Amazon S3
```

## Prerequisites

- **AWS Account**: Ensure you have an AWS account with access to Amazon Textract and Amazon Bedrock.
- **AWS CLI**: Install and configure the AWS CLI with appropriate credentials.
- **Python 3.8+**: Install Python and required dependencies.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/legal-document-analyzer.git
   cd legal-document-analyzer
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS**:
   Run the following command to configure your AWS credentials:
   ```bash
   aws configure
   ```

4. **Run the Application**:
   Execute the analysis script:
   ```bash
   python model.py
   ```

5. **View Results**:
   - The analysis results will be saved in `analysis_output.txt`.

## Key AWS Services Used

- **Amazon Textract**: Extracts text from uploaded documents.
- **Amazon Bedrock**: Uses the Nova model to analyze legal documents.

## Demo Video

[![Watch the demo](https://img.youtube.com/vi/H5KguBDQNEM/maxresdefault.jpg)](https://www.youtube.com/watch?v=H5KguBDQNEM)
https://youtu.be/

### Summary
- Governs use of OpenAI Technologies Inc. services.
- Agreement to Terms by using OpenAI's APIs, tools, models, or websites.

### Key Clauses
- **Introduction**: Establishes the governing terms for using OpenAI services.
- **Use of Services**: Ensures compliance with terms and laws.

### Risks
- **Termination Clause**: Broad right to terminate access at any time.
- **Indemnity Clause**: Heavy burden on users for claims or damages.

## References

- [Simple AI-Powered Legal Document Analyzer Using Amazon Nova](https://community.aws/content/2wm7rcuogUQowf2p9UjdXbnQmNs/simple-ai-powered-legal-document-analyzer-using-amazon-nova)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

**Disclaimer**: This tool is for informational purposes only and should not be used as a substitute for professional legal advice.

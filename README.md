# Coderoad AWS Final Project - S3 Presigned URL Generator

This project provides a serverless backend on AWS for generating S3 presigned URLs. It allows clients to securely upload and download files directly to and from an S3 bucket without needing AWS credentials.

## Architecture
![project architecture] (assets/project_architecture.png)
The architecture consists of the following components:

1.  **Amazon API Gateway:** Exposes two HTTP endpoints:
    *   `POST /files`: To request a presigned URL for uploading.
    *   `GET /files/{objectKey}`: To request a presigned URL for downloading.
2.  **AWS Lambda:** Contains the business logic for generating the presigned URLs.
    *   `GeneratePresignedUrlFunction`: Handles `POST /files` requests.
    *   `DownloadFileFunction`: Handles `GET /files/{objectKey}` requests.
3.  **Amazon S3:** The storage service for the files.
4.  **AWS IAM:** Provides the necessary permissions for the Lambda functions to access the S3 bucket.

The flow is as follows:
1. A client makes a request to API Gateway.
2. API Gateway invokes the appropriate Lambda function.
3. The Lambda function uses the AWS SDK to generate a presigned URL for S3.
4. The URL is returned to the client.
5. The client uses the URL to directly upload or download the file to/from S3.

## Project Structure

```
.
├── .github/workflows/deploy.yml   # GitHub Actions workflow for automated deployment
├── src/
│   ├── app.py                     # Lambda handler for generating upload URLs
│   └── download.py                # Lambda handler for generating download URLs
├── template.yaml                  # AWS SAM template defining the infrastructure
└── README.md                      # This documentation file
```

---

## Deployment

This application is deployed using the AWS Serverless Application Model (SAM).

### Automated Deployment (GitHub Actions)

The repository includes a GitHub Actions workflow that automatically deploys the application on every push to the `main` branch.

**Configuration:**
To use this, you must configure the following in your GitHub repository's settings:
1.  **OIDC Provider:** Set up an OIDC provider in your AWS account to trust GitHub.
2.  **IAM Role:** Create an IAM role named `githubconnect` that the GitHub Action can assume. This role needs permissions to deploy CloudFormation stacks and related resources.
3.  **GitHub Variables:** In your repository settings under `Settings > Secrets and variables > Actions`, create a repository variable named `AWS_ACCOUNT_ID` with your AWS Account ID.

### Manual Deployment

**Prerequisites:**
*   AWS CLI: Authenticated and configured with your AWS account.
*   AWS SAM CLI: Installed and configured.
*   Python 3.12: Installed.

**Steps:**

1.  **Build the SAM application:**
    This command packages the Lambda function code and dependencies.
    ```bash
    sam build
    ```

2.  **Deploy the application:**
    This command deploys the resources defined in `template.yaml` to your AWS account.
    ```bash
    sam deploy \
        --stack-name coderoad-final-aws-project \
        --region us-east-1 \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --resolve-s3 \
        --no-confirm-changeset
    ```

3.  **Get the API Endpoint:**
    After deployment, the API Gateway URL is displayed in the outputs. You can also retrieve it anytime using the AWS CLI:
    ```bash
    aws cloudformation describe-stacks \
        --stack-name coderoad-final-aws-project \
        --query "Stacks[0].Outputs[?OutputKey=='ApiBaseUrl'].OutputValue" \
        --output text
    ```

---

## Configuration Notes

*   **S3 Bucket:** The `template.yaml` defines an S3 bucket with a unique name: `coderoad-images-<YOUR_AWS_ACCOUNT_ID>-<YOUR_AWS_REGION>-final-project`. All public access to this bucket is blocked.
*   **IAM Permissions:** A dedicated IAM role (`coderoad-lambda-s3-role`) is created for the Lambda functions. It has a least-privilege policy attached, granting only `s3:PutObject`, `s3:GetObject`, and `s3:ListBucket` permissions on the created S3 bucket.
*   **Presigned URL Expiration:**
    *   **Upload URLs** are valid for **5 minutes** (300 seconds).
    *   **Download URLs** are valid for **1 hour** (3600 seconds).

---

## How to Test

You can test the API using `curl` or an API client like Postman.

### Using cURL

First, set a shell variable for your API base URL to make the commands easier:
```bash
export API_URL=$(aws cloudformation describe-stacks --stack-name coderoad-final-aws-project --query "Stacks[0].Outputs[?OutputKey=='ApiBaseUrl'].OutputValue" --output text)
echo "API URL set to: $API_URL"
```

**1. Get an Upload URL**

Request a presigned URL to upload a file named `my-test-file.txt`.

```bash
curl -X POST "$API_URL/files" \
  -H "Content-Type: application/json" \
  -d '{"fileName": "my-test-file.txt", "contentType": "text/plain"}'
```

The response will contain the `uploadUrl` and the `objectKey` for your file:
```json
{
  "uploadUrl": "https://...",
  "objectKey": "uploads/my-test-file.txt"
}
```

**2. Upload a File**

Create a dummy file and use the `uploadUrl` to upload it. **Important:** The URL must be wrapped in quotes.

```bash
echo "This is a test." > my-test-file.txt

# Copy the uploadUrl from the previous step
UPLOAD_URL="PASTE_THE_UPLOAD_URL_HERE"

curl -X PUT -T "my-test-file.txt" \
  -H "Content-Type: text/plain" \
  "$UPLOAD_URL"
```

**3. Download the File**

Use the `objectKey` to get a download link. The `curl -L` flag is important as it follows the HTTP 302 redirect to the presigned URL.

```bash
curl -L "$API_URL/files/uploads/my-test-file.txt"
```
This will print the content of the file to your console. To save to a file, use `-o`:
```bash
curl -L -o downloaded-file.txt "$API_URL/files/uploads/my-test-file.txt"
```

### Using Postman

1.  **Get Upload URL:**
    *   Create a `POST` request to `{{ApiBaseUrl}}/files`.
    *   In the `Body` tab, select `raw` and `JSON`.
    *   Add the body: `{"fileName": "your-file.jpg", "contentType": "image/jpeg"}`
    *   Set `ApiBaseUrl` as a Postman variable with the URL from the deployment outputs.
    *   Send the request and copy the `uploadUrl` from the response.

2.  **Upload File:**
    *   Create a `PUT` request and paste the copied `uploadUrl` as the request URL.
    *   In the `Body` tab, select `binary file` and choose the file you want to upload.
    *   In the `Headers` tab, add a `Content-Type` header matching your file (e.g., `image/jpeg`).
    *   Send the request.

3.  **Download File:**
    *   Create a `GET` request to `{{ApiBaseUrl}}/files/{{objectKey}}`.
    *   Replace `{{objectKey}}` with the `objectKey` from the first request (e.g., `uploads/your-file.jpg`).
    *   In Postman's settings, make sure "Follow redirects" is enabled.
    *   Sending the request will download the file.

---

## Cleaning Up

To avoid ongoing charges, you should delete the resources when you are finished. Run the following command to delete the entire CloudFormation stack:

```bash
aws cloudformation delete-stack --stack-name coderoad-final-aws-project
```
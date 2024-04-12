import pytest
import boto3
import requests
import os
from utils.aws_helpers import get_lambda_response, upload_to_s3, get_from_s3


API_BASE_URL = os.getenv("API_BASE_URL", "http://banking.aayulogic.internal")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


@pytest.fixture(scope="session")
def aws_clients():
    return {
        "lambda": boto3.client("lambda", region_name=AWS_REGION),
        "s3": boto3.client("s3", region_name=AWS_REGION),
        "rds": boto3.client("rds", region_name=AWS_REGION),
    }


@pytest.fixture(scope="session")
def api_token():
    response = requests.post(
        f"{API_BASE_URL}/api/auth/token",
        json={"email": "qatest@aayulogic.com", "password": "QATest@123"}
    )
    assert response.status_code == 200
    return response.json()["access"]


class TestAPIToLambdaFlow:
    """
    Integration tests validating the full flow:
    API request → Lambda processing → S3 storage → RDS persistence
    """

    def test_transaction_triggers_lambda(self, api_token, aws_clients):
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {"account_id": 1, "amount": 250.00, "type": "deposit"}
        response = requests.post(
            f"{API_BASE_URL}/api/transactions/deposit",
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        transaction_id = response.json()["transaction_id"]
        assert transaction_id is not None

    def test_transaction_receipt_stored_in_s3(self, api_token, aws_clients):
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {"account_id": 1, "amount": 100.00, "type": "deposit"}
        response = requests.post(
            f"{API_BASE_URL}/api/transactions/deposit",
            json=payload,
            headers=headers
        )
        transaction_id = response.json()["transaction_id"]
        s3_key = f"receipts/{transaction_id}.json"
        s3_obj = get_from_s3(aws_clients["s3"], os.getenv("S3_BUCKET_NAME"), s3_key)
        assert s3_obj is not None

    def test_api_response_within_sla(self, api_token):
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/accounts/1/balance",
            headers=headers
        )
        assert response.elapsed.total_seconds() < 1.5, "Response exceeded 1.5s SLA"

    def test_concurrent_requests_handled(self, api_token):
        import concurrent.futures
        headers = {"Authorization": f"Bearer {api_token}"}

        def make_request(_):
            return requests.get(
                f"{API_BASE_URL}/api/accounts/1/balance",
                headers=headers
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_request, range(5)))

        for r in results:
            assert r.status_code == 200


class TestCloudDeploymentHealth:

    def test_lambda_cold_start_acceptable(self, aws_clients):
        import json
        import time
        start = time.time()
        response = aws_clients["lambda"].invoke(
            FunctionName=os.getenv("LAMBDA_FUNCTION_NAME"),
            InvocationType="RequestResponse",
            Payload=json.dumps({"ping": True})
        )
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Cold start took {elapsed:.2f}s — too slow"

    def test_s3_bucket_accessible(self, aws_clients):
        response = aws_clients["s3"].head_bucket(
            Bucket=os.getenv("S3_BUCKET_NAME")
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
# flow tests
# s3 test
# sla tests

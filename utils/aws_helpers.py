import json
import boto3


def get_lambda_response(client, function_name, payload):
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload)
    )
    return json.loads(response["Payload"].read())


def upload_to_s3(client, bucket, key, data):
    if isinstance(data, dict):
        data = json.dumps(data)
    client.put_object(Bucket=bucket, Key=key, Body=data.encode("utf-8"))


def get_from_s3(client, bucket, key):
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return json.loads(response["Body"].read())
    except client.exceptions.NoSuchKey:
        return None


def check_rds_connection(host, database, user, password):
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=host, database=database, user=user, password=password
        )
        conn.close()
        return True
    except Exception:
        return False

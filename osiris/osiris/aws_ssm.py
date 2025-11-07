import boto3
import os

def get_ssm_parameter(name: str, decrypt: bool = True) -> str:
    ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION"))
    response = ssm.get_parameter(
        Name=name,
        WithDecryption=decrypt
    )
    return response["Parameter"]["Value"]

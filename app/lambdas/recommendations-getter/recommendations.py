import os
import boto3
import json
import logging
from decimal import Decimal
from boto3.dynamodb.conditions import Key

CORS_HEADERS = {
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            }

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def decimal_default(obj):
    if isinstance(obj, Decimal):
        # Convert to int if it's an integer value, else float
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Extract Cognito User ID from the API Gateway authorizer
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

        # Query DynamoDB for recommendations
        response = table.query(
            KeyConditionExpression=Key("CognitoUserID").eq(user_id)
        )

        # Return recommendations
        return {
            "statusCode": 200,
            'headers': CORS_HEADERS,
            "body": json.dumps(response.get("Items", []))
        }
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)}, default=decimal_default)
        }
import os
import boto3
import json
import logging
from boto3.dynamodb.conditions import Key

CORS_HEADERS = {
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,DELETE"
}

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        # Extract Cognito User ID from the API Gateway authorizer
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

        # Query DynamoDB for all items belonging to the user
        response = table.query(
            KeyConditionExpression=Key("CognitoUserID").eq(user_id)
        )

        # Delete each item
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                batch.delete_item(
                    Key={
                        "CognitoUserID": item["CognitoUserID"],
                        "creationTimestamp": item["creationTimestamp"]
                    }
                )

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "All recommendations deleted successfully."})
        }
    except Exception as e:
        logger.error(f"Error deleting recommendations: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }

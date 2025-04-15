import os
import boto3
import json
import logging

sns_client = boto3.client('sns')
sns_topic_arn = os.environ['SNS_TOPIC_ARN']


logger = logging.getLogger()
logger.setLevel(logging.INFO)

CORS_HEADERS = {
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            }

def lambda_handler(event, context):
    try:
        # Parse the input
        body = json.loads(event['body'])
        feedback_message = body['message']
        
        # Extract Cognito User ID from the API Gateway authorizer
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

        # Publish to SNS
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps({
                "userId": user_id,
                "message": feedback_message
            }),
            Subject="New Feedback"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Feedback sent successfully"}),
            "headers": CORS_HEADERS
        }
    except Exception as e:
        logger.error(f"Error sending feedback: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": CORS_HEADERS
        }

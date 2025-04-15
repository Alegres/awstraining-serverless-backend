import os
import boto3
import json
import logging
import time

# Initialize AWS clients
sqs_client = boto3.client('sqs')
dynamodb_client = boto3.resource('dynamodb')
bedrock_client = boto3.client('bedrock-runtime', region_name='eu-central-1')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
recommendations_table_name = os.environ['RECOMMENDATIONS_TABLE_NAME']
sqs_queue_url = os.environ['SQS_QUEUE_URL']  # Add this line to fetch the SQS queue URL

# DynamoDB table reference
recommendations_table = dynamodb_client.Table(recommendations_table_name)

bedrock_model_id = os.environ['BEDROCK_MODEL_ID']

def lambda_handler(event, context):
    try:
        # Process messages from SQS
        for record in event['Records']:
            message_body = json.loads(record['body'])
            inner_message = json.loads(message_body['Message'])

            user_id = inner_message['userId']
            feedback_message = inner_message['message']    

            bedrock_input = f"I have received the following feedback: {feedback_message}. Please provide a recommendation on how could I improve."

            # Call Amazon Bedrock for recommendation
            conversation = [
                {
                    "role": "user",
                    "content": [{"text": bedrock_input}],
                }
            ]

            bedrock_response = bedrock_client.converse(
                modelId=bedrock_model_id,
                messages=conversation,
                inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
            )
            response_text = bedrock_response["output"]["message"]["content"][0]["text"]

            # Save recommendation to DynamoDB
            recommendations_table.put_item(
                Item={
                    'CognitoUserID': user_id,
                    'recommendation': response_text,
                    'creationTimestamp': int(time.time() * 1000)  # Current timestamp in milliseconds
                }
            )

            # Delete the message from the SQS queue
            sqs_client.delete_message(
                QueueUrl=sqs_queue_url,
                ReceiptHandle=record['receiptHandle']
            )

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Recommendations processed successfully"})
        }
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

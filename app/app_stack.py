from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_event_sources
)
from constructs import Construct

class AppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # Reference an existing Cognito User Pool by ARN
        user_pool = cognito.UserPool.from_user_pool_arn(
            self, "ExistingUserPool",
            user_pool_arn="arn:aws:cognito-idp:eu-central-1:467331071075:userpool/eu-central-1_PkfzLNrOO"
        )

        # API Gateway
        api = apigateway.RestApi(
            self, "MyApi",
            rest_api_name="MySecureApi",
            description="API with Cognito Authorizer",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "OPTIONS", "DELETE", "POST"],
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Cognito Authorizer
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # Create DynamoDB Table
        recommendations_table = dynamodb.Table(
            self, "RecommendationsTable",
            table_name="Recommendations",
            partition_key=dynamodb.Attribute(
                name="CognitoUserID",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="creationTimestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Create Lambda Function to Retrieve Recommendations
        recommendations_lambda = _lambda.Function(
            self, "RecommendationsGetterLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="recommendations.lambda_handler",
            code=_lambda.Code.from_asset("app/lambdas/recommendations-getter"),
            environment={
                "TABLE_NAME": recommendations_table.table_name
            }
        )

        # Grant Lambda permissions to read from DynamoDB
        recommendations_table.grant_read_data(recommendations_lambda)

        # Add API Gateway Resource for /recommendations
        recommendations_resource = api.root.add_resource("recommendations")
        recommendations_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(recommendations_lambda),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        # Create Lambda Function to Delete Recommendations
        delete_recommendations_lambda = _lambda.Function(
            self, "RecommendationsDeleterLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="delete_recommendations.lambda_handler",
            code=_lambda.Code.from_asset("app/lambdas/recommendations-deleter"),
            environment={
                "TABLE_NAME": recommendations_table.table_name
            }
        )

        # Grant Lambda permissions to read & delete from DynamoDB
        recommendations_table.grant_write_data(delete_recommendations_lambda)
        recommendations_table.grant_read_data(delete_recommendations_lambda)

        # Add API Gateway Resource for /recommendations DELETE
        recommendations_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_recommendations_lambda),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        # Create SNS Topic
        feedback_topic = sns.Topic(
            self, "FeedbackTopic",
            display_name="Feedback Topic"
        )

        # Create SQS Queue
        feedback_queue = sqs.Queue(
            self, "FeedbackQueue",
            queue_name="FeedbackQueue"
        )

        # Subscribe SQS Queue to SNS Topic
        feedback_topic.add_subscription(subscriptions.SqsSubscription(feedback_queue))

        # Create Lambda Function to Send Feedback to SNS
        feedback_lambda = _lambda.Function(
            self, "FeedbackSenderLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="feedback.lambda_handler",
            code=_lambda.Code.from_asset("app/lambdas/feedback-sender"),
            environment={
                "SNS_TOPIC_ARN": feedback_topic.topic_arn
            }
        )

        # Grant Lambda permissions to publish to SNS
        feedback_topic.grant_publish(feedback_lambda)

        # Add API Gateway Resource for /feedback
        feedback_resource = api.root.add_resource("feedback")
        feedback_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(feedback_lambda),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        # Create Lambda Function to consume feedback from SQS
        # Placeholder for Bedrock model ID
        # Note: Replace 'your-bedrock-model-id' with the actual model ID from the Amazon Bedrock console.
        # To get the model ID:
        # 1. Go to the Amazon Bedrock console.
        # 2. Subscribe to a foundation model (e.g., AI21, Anthropic, or Stability AI).
        # 3. Copy the model ID from the Cros-Region Inference console (Amazon Bedrock -> Cross-region Inference), one with region included.
        feedback_consumer_lambda = _lambda.Function(
            self, "FeedbackConsumerLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="feedback_consumer.lambda_handler",
            code=_lambda.Code.from_asset("app/lambdas/feedback-consumer"),
            environment={
                "RECOMMENDATIONS_TABLE_NAME": recommendations_table.table_name,
                "SQS_QUEUE_URL": feedback_queue.queue_url,
                "BEDROCK_MODEL_ID": "eu.amazon.nova-micro-v1:0"  # Replace with actual Bedrock model ID
            }   
        )

        # Grant bedrock:InvokeModel permission to feedback_consumer Lambda
        feedback_consumer_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"]
            )
        )

        # Grant Lambda permissions to read from DynamoDB
        recommendations_table.grant_write_data(feedback_consumer_lambda)

        # Attach SQS as an event source for the feedback consumer Lambda
        feedback_consumer_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(feedback_queue)
        )

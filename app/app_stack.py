from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct

class AppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "AppQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        # Lambda Function
        hello_lambda = _lambda.Function(
            self, "HelloLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset("app/lambda")
        )

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
                allow_methods=["GET", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Cognito Authorizer
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # API Resource (e.g., /hello)
        hello_resource = api.root.add_resource("hello")
        
        hello_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(hello_lambda),
            authorization_type=apigateway.AuthorizationType.COGNITO,
            authorizer=authorizer
        )

        # Create DynamoDB Table
        recommendations_table = dynamodb.Table(
            self, "RecommendationsTable",
            table_name="FeedbackRecommendations",
            partition_key=dynamodb.Attribute(
                name="CognitoUserID",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="creationTimestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Create Lambda Function to Retrieve Recommendations
        recommendations_lambda = _lambda.Function(
            self, "RecommendationsLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="recommendations.lambda_handler",
            code=_lambda.Code.from_asset("app/lambda-recommendations"),
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

        # DynamoDB Table (TODO)
        

        # Lambda IAM role

        # Second Lambda calling Bedrock and writing to DynamoDB

        # SNS

        # SQS

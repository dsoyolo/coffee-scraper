"""Lambda + API Gateway for the FastAPI backend."""
from pathlib import Path

from aws_cdk import Duration
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from constructs import Construct

_BACKEND_DIR = str(Path(__file__).parent.parent.parent / "backend")


class BackendStack(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        products_table: dynamodb.Table,
        history_table: dynamodb.Table,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        env_vars = {
            "DYNAMO_PRODUCTS_TABLE": products_table.table_name,
            "DYNAMO_HISTORY_TABLE": history_table.table_name,
            "AWS_REGION": "eu-west-1",
        }

        # uv exports production deps; pip installs them into the Lambda package dir.
        _bundle_cmd = (
            "pip install uv --quiet"
            " && uv export --frozen --no-dev --no-hashes -o /tmp/requirements.txt"
            " && pip install -r /tmp/requirements.txt -t /asset-output --quiet"
            " && cp -r . /asset-output"
        )
        _bundling = {
            "image": _lambda.Runtime.PYTHON_3_12.bundling_image,
            "command": ["bash", "-c", _bundle_cmd],
        }

        # API Lambda — serves FastAPI app
        self.api_function = _lambda.Function(
            self,
            "ApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=_lambda.Code.from_asset(_BACKEND_DIR, bundling=_bundling),
            memory_size=512,
            timeout=Duration.seconds(30),
            environment=env_vars,
            log_retention=logs.RetentionDays.TWO_WEEKS,
        )

        # Scraper Lambda — same code, triggered by EventBridge
        self.scraper_function = _lambda.Function(
            self,
            "ScraperFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=_lambda.Code.from_asset(_BACKEND_DIR, bundling=_bundling),
            memory_size=512,
            timeout=Duration.minutes(5),
            environment=env_vars,
            log_retention=logs.RetentionDays.TWO_WEEKS,
        )

        # Grant DynamoDB access
        for fn in (self.api_function, self.scraper_function):
            products_table.grant_read_write_data(fn)
            history_table.grant_read_write_data(fn)

        # API Gateway
        self.api = apigw.LambdaRestApi(
            self,
            "CoffeeApi",
            handler=self.api_function,
            proxy=True,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )

        # EventBridge rule — run scraper every day at 07:00 UTC
        rule = events.Rule(
            self,
            "DailyScraperRule",
            schedule=events.Schedule.cron(hour="7", minute="0"),
            description="Trigger coffee scraper daily at 07:00 UTC",
        )
        rule.add_target(targets.LambdaFunction(self.scraper_function))

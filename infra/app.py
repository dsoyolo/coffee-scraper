#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.main_stack import CoffeeAggregatorStack

app = cdk.App()

CoffeeAggregatorStack(
    app,
    "CoffeeAggregatorStack",
    env=cdk.Environment(
        # Set via environment variables or change to your account/region
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "eu-west-1",
    ),
    description="Coffee Price Aggregator — FastAPI + DynamoDB + React on AWS",
)

app.synth()

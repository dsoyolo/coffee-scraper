"""DynamoDB tables for products and price history."""
from aws_cdk import RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class DatabaseStack(Construct):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Products table — product_id is the partition key
        self.products_table = dynamodb.Table(
            self,
            "ProductsTable",
            table_name="coffee-products",
            partition_key=dynamodb.Attribute(
                name="product_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Price history table — partition by product_id, sort by scraped_at
        self.history_table = dynamodb.Table(
            self,
            "HistoryTable",
            table_name="coffee-price-history",
            partition_key=dynamodb.Attribute(
                name="product_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="scraped_at",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # Keep 90 days of history with TTL
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.RETAIN,
        )

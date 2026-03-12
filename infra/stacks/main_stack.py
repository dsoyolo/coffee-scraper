"""Top-level CDK stack that wires everything together."""
import aws_cdk as cdk
from constructs import Construct

from stacks.backend import BackendStack
from stacks.database import DatabaseStack
from stacks.frontend import FrontendStack


class CoffeeAggregatorStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        db = DatabaseStack(self, "Database")

        backend = BackendStack(
            self,
            "Backend",
            products_table=db.products_table,
            history_table=db.history_table,
        )

        FrontendStack(
            self,
            "Frontend",
            api_url=backend.api.url,
        )

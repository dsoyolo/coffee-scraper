"""S3 + CloudFront for the React SPA."""
from pathlib import Path

from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct

_FRONTEND_DIST = str(Path(__file__).parent.parent.parent / "frontend" / "dist")


class FrontendStack(Construct):
    def __init__(self, scope: Construct, id: str, api_url: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 bucket — no public access, served only via CloudFront
        bucket = s3.Bucket(
            self,
            "SiteBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # CloudFront Origin Access Control
        oac = cloudfront.S3OriginAccessControl(self, "OAC")

        # CloudFront distribution
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    bucket,
                    origin_access_control=oac,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                # SPA routing — serve index.html for all 403/404
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
        )

        # Deploy built frontend assets
        s3deploy.BucketDeployment(
            self,
            "DeployFrontend",
            sources=[s3deploy.Source.asset(_FRONTEND_DIST)],
            destination_bucket=bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        CfnOutput(
            self,
            "CloudFrontUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="Coffee Price Aggregator frontend URL",
        )

        CfnOutput(
            self,
            "ApiUrl",
            value=api_url,
            description="Backend API URL",
        )

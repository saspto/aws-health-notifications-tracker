from aws_cdk import Stack, CfnOutput
from constructs import Construct
from .constructs.storage import StorageConstruct
from .constructs.lambdas import LambdasConstruct
from .constructs.api import ApiConstruct
from .constructs.distribution import DistributionConstruct


class HealthTrackerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        admin_email = self.node.try_get_context("admin_email") or "ops-team@example.com"

        storage = StorageConstruct(self, "Storage")
        lambdas = LambdasConstruct(self, "Lambdas", storage=storage, admin_email=admin_email)
        api = ApiConstruct(self, "Api", api_handler=lambdas.api_handler)
        distribution = DistributionConstruct(
            self, "Distribution", frontend_bucket=storage.frontend_bucket, api=api.http_api
        )

        CfnOutput(self, "CloudFrontURL", value=f"https://{distribution.distribution.distribution_domain_name}")
        CfnOutput(self, "UserPoolId", value=api.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=api.user_pool_client.user_pool_client_id)
        CfnOutput(self, "ApiEndpoint", value=api.http_api.url or "")
        CfnOutput(self, "TableName", value=storage.table.table_name)
        CfnOutput(self, "FrontendBucketName", value=storage.frontend_bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution.distribution_id)

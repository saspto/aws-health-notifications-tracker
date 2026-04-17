from aws_cdk import (
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_apigatewayv2 as apigw,
    Duration,
)
from constructs import Construct


class DistributionConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        frontend_bucket: s3.Bucket,
        api: apigw.HttpApi,
    ) -> None:
        super().__init__(scope, construct_id)

        oac = cloudfront.S3OriginAccessControl(
            self,
            "OAC",
            description="OAC for Health Tracker frontend",
        )

        s3_origin = origins.S3BucketOrigin.with_origin_access_control(
            frontend_bucket,
            origin_access_control=oac,
        )

        api_url = api.url or ""
        api_domain = api_url.replace("https://", "").rstrip("/").split("/")[0]
        api_path = "/" + "/".join(api_url.replace("https://", "").rstrip("/").split("/")[1:])

        api_origin = origins.HttpOrigin(
            api_domain,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
        )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress=True,
                cache_policy=cloudfront.CachePolicy(
                    self,
                    "StaticCachePolicy",
                    default_ttl=Duration.seconds(3600),
                    max_ttl=Duration.seconds(86400),
                    min_ttl=Duration.seconds(0),
                    enable_accept_encoding_gzip=True,
                    enable_accept_encoding_brotli=True,
                ),
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=api_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                )
            },
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_page_path="/index.html",
                    response_http_status=200,
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_page_path="/index.html",
                    response_http_status=200,
                ),
            ],
        )

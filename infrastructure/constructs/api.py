from aws_cdk import (
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_lambda as lambda_,
    Duration,
)
from constructs import Construct


class ApiConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, api_handler: lambda_.Function
    ) -> None:
        super().__init__(scope, construct_id)

        lambda_integration = integrations.HttpLambdaIntegration(
            "ApiHandlerIntegration", api_handler
        )

        self.http_api = apigw.HttpApi(
            self,
            "HealthTrackerApi",
            api_name="health-tracker-api",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_headers=["Content-Type", "Authorization"],
                allow_methods=[
                    apigw.CorsHttpMethod.GET,
                    apigw.CorsHttpMethod.PATCH,
                    apigw.CorsHttpMethod.OPTIONS,
                ],
                allow_origins=["*"],
                max_age=Duration.days(1),
            ),
        )

        routes = [
            ("GET", "/events"),
            ("GET", "/events/{eventArn}/{accountId}"),
            ("PATCH", "/events/{eventArn}/{accountId}"),
            ("GET", "/stats"),
            ("GET", "/accounts"),
        ]

        for method_str, path in routes:
            method = getattr(apigw.HttpMethod, method_str)
            self.http_api.add_routes(
                path=path,
                methods=[method],
                integration=lambda_integration,
            )

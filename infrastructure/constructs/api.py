from aws_cdk import (
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_apigatewayv2_authorizers as authorizers,
    aws_cognito as cognito,
    aws_lambda as lambda_,
    Duration,
)
from constructs import Construct


class ApiConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, api_handler: lambda_.Function
    ) -> None:
        super().__init__(scope, construct_id)

        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name="health-tracker-users",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            removal_policy=__import__("aws_cdk").RemovalPolicy.DESTROY,
        )

        self.user_pool_client = self.user_pool.add_client(
            "WebClient",
            user_pool_client_name="health-tracker-web",
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(implicit_code_grant=True),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
            ),
        )

        lambda_integration = integrations.HttpLambdaIntegration(
            "ApiHandlerIntegration", api_handler
        )

        jwt_authorizer = authorizers.HttpJwtAuthorizer(
            "CognitoAuthorizer",
            jwt_issuer=f"https://cognito-idp.us-east-1.amazonaws.com/{self.user_pool.user_pool_id}",
            jwt_audience=[self.user_pool_client.user_pool_client_id],
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
                authorizer=jwt_authorizer,
            )

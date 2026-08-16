"""KittyNails infrastructure stack.

Architecture:
- VPC with public + private subnets, egress via a cheap NAT *instance* (t4g.nano)
  instead of a managed NAT Gateway.
- RDS PostgreSQL t4g.micro in private subnets, no public access.
- Secrets Manager holds the DB credentials (auto-generated) and app secrets.
- Backend Lambda (FastAPI via Mangum) + reminder Lambda, both in the VPC,
  packaged as a container image.
- REST API Gateway proxies to the backend Lambda.
- EventBridge rule triggers the reminder Lambda hourly.
- S3 + CloudFront serve the React frontend; /api/* is routed to API Gateway.
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigw,
)
from aws_cdk import (
    aws_cloudfront as cloudfront,
)
from aws_cdk import (
    aws_cloudfront_origins as origins,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_rds as rds,
)
from aws_cdk import (
    aws_s3 as s3,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

# Bedrock inference profile used by the app (EU geo routing).
BEDROCK_MODEL_ID = "eu.anthropic.claude-sonnet-4-6"
# The repo root, relative to this file (infra/), is the Docker build context.
DOCKER_CONTEXT = ".."
LAMBDA_DOCKERFILE = "Dockerfile.lambda"


class KittyNailsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = self._create_vpc()
        db, db_secret = self._create_database(vpc)
        app_secret = self._create_app_secret()
        backend_fn = self._create_backend_lambda(vpc, db, db_secret, app_secret)
        self._create_reminder_lambda(vpc, db, db_secret, app_secret)
        api = self._create_api_gateway(backend_fn)
        self._create_frontend(api)

    # ------------------------------------------------------------------ VPC
    def _create_vpc(self) -> ec2.Vpc:
        # Use a NAT *instance* (t4g.nano) instead of a NAT Gateway to save ~$28/mo.
        nat_provider = ec2.NatProvider.instance_v2(
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.NANO
            ),
        )

        vpc = ec2.Vpc(
            self,
            "KittyNailsVpc",
            max_azs=2,
            nat_gateway_provider=nat_provider,
            nat_gateways=1,  # single NAT instance to keep costs low
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )
        return vpc

    # ------------------------------------------------------------- Database
    def _create_database(
        self, vpc: ec2.Vpc
    ) -> tuple[rds.DatabaseInstance, secretsmanager.ISecret]:
        db = rds.DatabaseInstance(
            self,
            "KittyNailsDb",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            # Never expose the DB to the internet.
            publicly_accessible=False,
            allocated_storage=20,
            max_allocated_storage=50,
            # Auto-generate credentials and store them in Secrets Manager.
            credentials=rds.Credentials.from_generated_secret(
                "kitty", secret_name="kittynails/db"
            ),
            database_name="kittynails",
            backup_retention=Duration.days(7),
            deletion_protection=True,
            removal_policy=RemovalPolicy.SNAPSHOT,
        )
        return db, db.secret

    # ----------------------------------------------------------- App secret
    def _create_app_secret(self) -> secretsmanager.Secret:
        # App-level secrets. Values are populated after deploy (see README).
        # We seed a generated JWT secret; the rest are placeholders you fill in.
        return secretsmanager.Secret(
            self,
            "KittyNailsAppSecret",
            secret_name="kittynails/app",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=(
                    '{"ADMIN_USERNAME":"cata",'
                    '"ADMIN_PASSWORD_HASH":"",'
                    '"STRIPE_SECRET_KEY":"",'
                    '"STRIPE_PUBLISHABLE_KEY":"",'
                    '"STRIPE_WEBHOOK_SECRET":""}'
                ),
                generate_string_key="JWT_SECRET",
                exclude_punctuation=True,
                password_length=64,
            ),
        )

    # -------------------------------------------------------- Backend Lambda
    def _create_backend_lambda(
        self,
        vpc: ec2.Vpc,
        db: rds.DatabaseInstance,
        db_secret: secretsmanager.ISecret,
        app_secret: secretsmanager.Secret,
    ) -> lambda_.DockerImageFunction:
        fn = lambda_.DockerImageFunction(
            self,
            "BackendFn",
            code=lambda_.DockerImageCode.from_image_asset(
                directory=DOCKER_CONTEXT,
                file=LAMBDA_DOCKERFILE,
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            memory_size=1024,
            timeout=Duration.seconds(30),
            environment=self._common_env(db, db_secret, app_secret),
        )

        self._grant_common(fn, db, db_secret, app_secret)
        return fn

    # ------------------------------------------------------- Reminder Lambda
    def _create_reminder_lambda(
        self,
        vpc: ec2.Vpc,
        db: rds.DatabaseInstance,
        db_secret: secretsmanager.ISecret,
        app_secret: secretsmanager.Secret,
    ) -> lambda_.DockerImageFunction:
        fn = lambda_.DockerImageFunction(
            self,
            "ReminderFn",
            code=lambda_.DockerImageCode.from_image_asset(
                directory=DOCKER_CONTEXT,
                file=LAMBDA_DOCKERFILE,
                cmd=["src.reminder_handler.handler"],
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            memory_size=512,
            timeout=Duration.minutes(2),
            environment=self._common_env(db, db_secret, app_secret),
        )

        self._grant_common(fn, db, db_secret, app_secret)

        # Trigger hourly. The handler queries a 23-25h window so each
        # appointment is reminded exactly once.
        rule = events.Rule(
            self,
            "ReminderSchedule",
            schedule=events.Schedule.rate(Duration.hours(1)),
        )
        rule.add_target(targets.LambdaFunction(fn))
        return fn

    # -------------------------------------------------------- API Gateway
    def _create_api_gateway(
        self, backend_fn: lambda_.DockerImageFunction
    ) -> apigw.LambdaRestApi:
        api = apigw.LambdaRestApi(
            self,
            "KittyNailsApi",
            handler=backend_fn,
            proxy=True,
            deploy_options=apigw.StageOptions(stage_name="prod"),
            binary_media_types=["*/*"],  # allow image uploads for nail analysis
        )
        CfnOutput(self, "ApiUrl", value=api.url)
        return api

    # ----------------------------------------------------------- Frontend
    def _create_frontend(self, api: apigw.LambdaRestApi) -> None:
        bucket = s3.Bucket(
            self,
            "FrontendBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # API Gateway origin: strip the stage from the domain and use the path.
        api_domain = f"{api.rest_api_id}.execute-api.{self.region}.amazonaws.com"

        distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        api_domain,
                        origin_path="/prod",
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                ),
            },
            default_root_object="index.html",
            # SPA routing: serve index.html for client-side routes.
            error_responses=[
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

        CfnOutput(self, "FrontendBucketName", value=bucket.bucket_name)
        CfnOutput(
            self,
            "CloudFrontUrl",
            value=f"https://{distribution.distribution_domain_name}",
        )

    # ------------------------------------------------------------- Helpers
    def _common_env(
        self,
        db: rds.DatabaseInstance,
        db_secret: secretsmanager.ISecret,
        app_secret: secretsmanager.Secret,
    ) -> dict:
        return {
            "DB_SECRET_ARN": db_secret.secret_arn,
            "APP_SECRET_ARN": app_secret.secret_arn,
            "DB_HOST": db.db_instance_endpoint_address,
            "DB_PORT": db.db_instance_endpoint_port,
            "DB_NAME": "kittynails",
            "AWS_REGION_NAME": self.region,
            "NAIL_ANALYSIS_MODEL": BEDROCK_MODEL_ID,
            "SES_ENABLED": "true",
        }

    def _grant_common(
        self,
        fn: lambda_.DockerImageFunction,
        db: rds.DatabaseInstance,
        db_secret: secretsmanager.ISecret,
        app_secret: secretsmanager.Secret,
    ) -> None:
        # DB network access
        db.connections.allow_default_port_from(fn)
        # Read secrets
        db_secret.grant_read(fn)
        app_secret.grant_read(fn)
        # Bedrock (nail analysis)
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )
        # SES (confirmation + reminder emails)
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )

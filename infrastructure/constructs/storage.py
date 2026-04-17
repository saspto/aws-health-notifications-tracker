from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    RemovalPolicy,
    Duration,
)
from constructs import Construct


class StorageConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.table = dynamodb.Table(
            self,
            "HealthEventsTable",
            table_name="HealthEvents",
            partition_key=dynamodb.Attribute(name="eventArn", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="accountId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
            point_in_time_recovery=True,
        )

        self.table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(name="service", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="startTime", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        self.table.add_global_secondary_index(
            index_name="GSI2",
            partition_key=dynamodb.Attribute(name="urgency", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="deadline", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        self.table.add_global_secondary_index(
            index_name="GSI3",
            partition_key=dynamodb.Attribute(name="status", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="startTime", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        self.archive_bucket = s3.Bucket(
            self,
            "ArchiveBucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        )
                    ]
                )
            ],
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

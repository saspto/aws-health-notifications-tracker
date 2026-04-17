from aws_cdk import (
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_lambda_event_sources as lambda_event_sources,
    aws_scheduler as scheduler,
    Duration,
    Stack,
)
from constructs import Construct
from .storage import StorageConstruct
import os


class LambdasConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, storage: StorageConstruct, admin_email: str
    ) -> None:
        super().__init__(scope, construct_id)

        account_id = Stack.of(self).account
        region = Stack.of(self).region

        base_env = {
            "TABLE_NAME": storage.table.table_name,
            "ARCHIVE_BUCKET": storage.archive_bucket.bucket_name,
            "REGION": region,
        }

        # Health Collector Lambda
        self.health_collector = lambda_.Function(
            self,
            "HealthCollector",
            function_name="health-collector",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambdas/health_collector"),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment=base_env,
        )

        storage.table.grant_read_write_data(self.health_collector)
        storage.archive_bucket.grant_write(self.health_collector)

        self.health_collector.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "health:DescribeEventsForOrganization",
                    "health:DescribeEventDetailsForOrganization",
                    "health:DescribeAffectedAccountsForOrganizationEvent",
                    "health:DescribeAffectedEntitiesForOrganization",
                    "organizations:ListAccounts",
                ],
                resources=["*"],
            )
        )

        # LLM Summarizer Lambda
        self.llm_summarizer = lambda_.Function(
            self,
            "LlmSummarizer",
            function_name="llm-summarizer",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambdas/llm_summarizer"),
            timeout=Duration.minutes(2),
            memory_size=256,
            environment=base_env,
        )

        storage.table.grant_write_data(self.llm_summarizer)

        self.llm_summarizer.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
                ],
            )
        )

        self.llm_summarizer.add_event_source(
            lambda_event_sources.DynamoEventSource(
                storage.table,
                starting_position=lambda_.StartingPosition.TRIM_HORIZON,
                batch_size=10,
                filters=[
                    lambda_.FilterCriteria.filter(
                        {
                            "eventName": lambda_.FilterRule.or_("INSERT", "MODIFY"),
                        }
                    )
                ],
            )
        )

        # Deadline Reminder Lambda
        self.sns_topic = sns.Topic(
            self,
            "HealthDeadlineAlerts",
            topic_name="HealthDeadlineAlerts",
            display_name="AWS Health Deadline Alerts",
        )

        self.sns_topic.add_subscription(sns_subscriptions.EmailSubscription(admin_email))

        self.deadline_reminder = lambda_.Function(
            self,
            "DeadlineReminder",
            function_name="deadline-reminder",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambdas/deadline_reminder"),
            timeout=Duration.minutes(1),
            memory_size=128,
            environment={
                **base_env,
                "SNS_TOPIC_ARN": self.sns_topic.topic_arn,
            },
        )

        storage.table.grant_read_data(self.deadline_reminder)
        self.sns_topic.grant_publish(self.deadline_reminder)

        self.deadline_reminder.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        # API Handler Lambda
        self.api_handler = lambda_.Function(
            self,
            "ApiHandler",
            function_name="api-handler",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambdas/api_handler"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment=base_env,
        )

        storage.table.grant_read_write_data(self.api_handler)

        # EventBridge Scheduler role
        scheduler_role = iam.Role(
            self,
            "SchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )

        self.health_collector.grant_invoke(scheduler_role)
        self.deadline_reminder.grant_invoke(scheduler_role)

        # Health collector schedule (every 15 minutes)
        scheduler.CfnSchedule(
            self,
            "HealthCollectorSchedule",
            name="health-collector-schedule",
            schedule_expression="rate(15 minutes)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.health_collector.function_arn,
                role_arn=scheduler_role.role_arn,
            ),
        )

        # Deadline reminder schedule (daily at 09:00 UTC)
        scheduler.CfnSchedule(
            self,
            "DeadlineReminderSchedule",
            name="deadline-reminder-schedule",
            schedule_expression="cron(0 9 * * ? *)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.deadline_reminder.function_arn,
                role_arn=scheduler_role.role_arn,
            ),
        )

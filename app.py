#!/usr/bin/env python3
import aws_cdk as cdk
from infrastructure.stack import HealthTrackerStack

app = cdk.App()
HealthTrackerStack(
    app,
    "HealthTrackerStack",
    env=cdk.Environment(region="us-east-1"),
)
app.synth()

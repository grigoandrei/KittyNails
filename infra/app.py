#!/usr/bin/env python3
"""CDK app entry point for KittyNails infrastructure."""

import os

import aws_cdk as cdk

from kitty_nails_stack import KittyNailsStack

app = cdk.App()

KittyNailsStack(
    app,
    "KittyNailsStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "eu-central-1"),
    ),
    description="KittyNails nail salon booking app — backend Lambda, RDS, frontend",
)

app.synth()

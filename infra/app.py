#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.infra_stack import DailyCheckinStack


app = cdk.App()

# 環境パラメータの取得（デフォルト値付き）
environment = app.node.try_get_context("environment") or "dev"
project_name = app.node.try_get_context("project_name") or "daily-checkin"

# LocalStack環境の場合の特別な設定
if environment == "local":
    # LocalStack用の環境変数設定
    os.environ.setdefault("CDK_DEFAULT_REGION", "us-east-1")
    os.environ.setdefault("CDK_DEFAULT_ACCOUNT", "000000000000")  # LocalStackのデフォルトアカウント

# CDKスタックの作成
DailyCheckinStack(
    app, 
    f"DailyCheckin-{environment.title()}Stack",
    environment=environment,
    project_name=project_name,
    # AWS環境の設定
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
        region=os.getenv('CDK_DEFAULT_REGION') or 'us-east-1'
    ),
)

app.synth()

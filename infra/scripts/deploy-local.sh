#!/bin/bash

# LocalStack環境へのCDKデプロイメントスクリプト

echo "🚀 Deploying CDK stack to LocalStack..."

# LocalStackエンドポイントの設定
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# CDKブートストラップ（初回のみ必要）
echo "📦 Bootstrapping CDK for LocalStack..."
cdklocal bootstrap

# CDKスタックのデプロイ
echo "🔧 Deploying DailyCheckin stack..."
cdklocal deploy DailyCheckinStack-local --require-approval never

echo "✅ Deployment completed!"
echo ""
echo "📋 Stack outputs:"
cdklocal list --long
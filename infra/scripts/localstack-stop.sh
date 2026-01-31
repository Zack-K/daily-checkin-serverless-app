#!/bin/bash

# LocalStack開発環境停止スクリプト

echo "🛑 Stopping LocalStack..."

# LocalStackコンテナを停止・削除
docker-compose -f docker-compose.localstack.yml down

echo "✅ LocalStack stopped successfully!"
echo ""
echo "💡 To start again: ./scripts/localstack-start.sh"
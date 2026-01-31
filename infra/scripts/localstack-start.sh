#!/bin/bash

# LocalStack開発環境起動スクリプト

echo "🚀 Starting LocalStack for Daily Checkin App..."

# LocalStackコンテナを起動
docker-compose -f docker-compose.localstack.yml up -d

# LocalStackが起動するまで待機
echo "⏳ Waiting for LocalStack to be ready..."
until curl -s http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; do
    echo "   Waiting for LocalStack services..."
    sleep 2
done

echo "✅ LocalStack is ready!"
echo ""
echo "📋 Available services:"
echo "   - S3: http://localhost:4566"
echo "   - DynamoDB: http://localhost:4566"
echo "   - Lambda: http://localhost:4566"
echo "   - CloudFormation: http://localhost:4566"
echo ""
echo "🔧 Next steps:"
echo "   1. Deploy CDK stack: npm run deploy:local"
echo "   2. Run tests: npm run test:local"
echo "   3. Stop LocalStack: npm run localstack:stop"
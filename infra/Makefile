# Daily Checkin CDK Infrastructure Makefile

.PHONY: help install localstack-start localstack-stop deploy-local deploy-dev test clean

# デフォルトターゲット
help:
	@echo "Daily Checkin CDK Infrastructure"
	@echo ""
	@echo "Available commands:"
	@echo "  install         - Install dependencies"
	@echo "  localstack-start - Start LocalStack for local development"
	@echo "  localstack-stop  - Stop LocalStack"
	@echo "  deploy-local    - Deploy to LocalStack"
	@echo "  deploy-dev      - Deploy to AWS dev environment"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up generated files"

# 依存関係のインストール
install:
	@echo "📦 Installing dependencies..."
	pip install -e ".[dev,local]"

# LocalStack環境
localstack-start:
	@echo "🚀 Starting LocalStack..."
	./scripts/localstack-start.sh

localstack-stop:
	@echo "🛑 Stopping LocalStack..."
	./scripts/localstack-stop.sh

# デプロイメント
deploy-local:
	@echo "🚀 Deploying to LocalStack..."
	cdk deploy --context environment=local --require-approval never

deploy-dev:
	@echo "🚀 Deploying to AWS dev environment..."
	cdk deploy --context environment=dev --require-approval never

# テスト
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

test-local:
	@echo "🧪 Running tests against LocalStack..."
	pytest tests/ -v --environment=local

# クリーンアップ
clean:
	@echo "🧹 Cleaning up..."
	rm -rf cdk.out/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf **/__pycache__/

# 開発環境のセットアップ（初回のみ）
setup-dev: install localstack-start
	@echo "✅ Development environment setup complete!"
	@echo "   Run 'make deploy-local' to deploy to LocalStack"
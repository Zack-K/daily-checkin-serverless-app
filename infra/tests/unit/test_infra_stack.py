import aws_cdk as core
import aws_cdk.assertions as assertions

from infra.infra_stack import DailyCheckinStack

def test_dynamodb_table_created():
    """Test that DynamoDB table is created with correct configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test DynamoDB table creation with correct properties
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "DailyHealthLog",
        "AttributeDefinitions": [
            {
                "AttributeName": "Date",
                "AttributeType": "S"
            },
            {
                "AttributeName": "Period",
                "AttributeType": "S"
            }
        ],
        "KeySchema": [
            {
                "AttributeName": "Date",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "Period",
                "KeyType": "RANGE"
            }
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "PointInTimeRecoverySpecification": {
            "PointInTimeRecoveryEnabled": True
        }
    })

def test_stack_creation():
    """Test basic stack creation"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify that the stack can be created without errors
    assert template is not None

def test_s3_bucket_deployment_created():
    """Test that S3 bucket deployment is created with correct configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test that BucketDeployment resource is created
    # 要件 1.2: 既存のS3/index.htmlファイルを新しいバケットにデプロイする機能を提供
    template.resource_count_is("Custom::CDKBucketDeployment", 1)

def test_s3_bucket_created():
    """Test that S3 bucket is created with correct configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test S3 bucket creation with versioning enabled
    # 要件 1.1, 1.4: バケット作成とバージョニング有効
    template.has_resource_properties("AWS::S3::Bucket", {
        "VersioningConfiguration": {
            "Status": "Enabled"
        }
    })

def test_lambda_function_url_created():
    """Test that Lambda Function URL is created with correct configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test Lambda Function URL creation
    # 要件 4.1-4.4: Function URL設定
    template.resource_count_is("AWS::Lambda::Url", 1)
    template.has_resource_properties("AWS::Lambda::Url", {
        "AuthType": "NONE",
        "Cors": {
            "AllowMethods": ["POST"],
            "AllowOrigins": ["*"],  # test環境では全てのオリジンを許可
            "AllowHeaders": ["Content-Type", "X-Requested-With"]
        }
    })

def test_cdk_outputs_created():
    """Test that CDK outputs are created"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test that outputs are created
    # 要件 7.5: 重要なリソース識別子の出力
    template.has_output("CloudFrontURL", {})
    template.has_output("LambdaFunctionURL", {})
    template.has_output("S3BucketName", {})
    template.has_output("DynamoDBTableName", {})

def test_lambda_function_created():
    """Test that Lambda function is created with correct configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test Lambda function creation (BucketDeploymentも1つのLambda関数を作成するため、合計2つ)
    # 要件 3.1-3.5: Lambda関数設定
    template.resource_count_is("AWS::Lambda::Function", 2)
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.12",
        "Handler": "submit_daily_checkin.lambda_handler",
        "Timeout": 30,
        "MemorySize": 128
    })

def test_iam_role_created():
    """Test that IAM role is created with correct permissions"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test IAM role creation (BucketDeploymentも1つのIAMロールを作成するため、合計2つ)
    # 要件 6.1-6.3: IAMセキュリティ設定
    template.resource_count_is("AWS::IAM::Role", 2)
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    }
                }
            ]
        }
    })

def test_environment_specific_configuration():
    """Test environment-specific configuration"""
    # 各環境で別々のAppを作成してsynthesis問題を回避
    local_app = core.App()
    local_stack = DailyCheckinStack(local_app, "local-stack", environment="local", project_name="test-project")
    local_template = assertions.Template.from_stack(local_stack)
    
    dev_app = core.App()
    dev_stack = DailyCheckinStack(dev_app, "dev-stack", environment="dev", project_name="test-project")
    dev_template = assertions.Template.from_stack(dev_stack)
    
    prod_app = core.App()
    prod_stack = DailyCheckinStack(prod_app, "prod-stack", environment="prod", project_name="test-project")
    prod_template = assertions.Template.from_stack(prod_stack)
    
    # Verify that stacks can be created for different environments
    assert local_template is not None
    assert dev_template is not None
    assert prod_template is not None

def test_resource_naming_convention():
    """Test that resources follow consistent naming convention"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="my-project")
    template = assertions.Template.from_stack(stack)

    # Test S3 bucket naming
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketName": "my-project-test-static-website"
    })

def test_tags_applied():
    """Test that common tags are applied to resources"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="my-project")
    template = assertions.Template.from_stack(stack)
    
    # Verify tags are applied to S3 bucket (必要なタグのみをチェック)
    template.has_resource_properties("AWS::S3::Bucket", {
        "Tags": assertions.Match.array_with([
            {"Key": "Environment", "Value": "test"},
            {"Key": "Project", "Value": "my-project"}
        ])
    })

def test_s3_bucket_security_configuration():
    """Test S3 bucket security configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test", project_name="test-project")
    template = assertions.Template.from_stack(stack)

    # Test S3 bucket security settings - 全4つのパブリックアクセスブロック設定をテスト
    # 要件 1.3, 1.5: セキュリティベストプラクティス
    template.has_resource_properties("AWS::S3::Bucket", {
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True,
            "BlockPublicPolicy": True,
            "IgnorePublicAcls": True,
            "RestrictPublicBuckets": True
        }
    })

def test_cors_configuration_environment_aware():
    """Test that CORS configuration is environment-aware"""
    # Test development environment (allows all origins)
    dev_app = core.App()
    dev_stack = DailyCheckinStack(dev_app, "dev-stack", environment="dev", project_name="test-project")
    dev_template = assertions.Template.from_stack(dev_stack)
    
    dev_template.has_resource_properties("AWS::Lambda::Url", {
        "Cors": {
            "AllowOrigins": ["*"]
        }
    })
    
    # Test production environment (restricted origins)
    prod_app = core.App()
    prod_stack = DailyCheckinStack(prod_app, "prod-stack", environment="prod", project_name="test-project")
    prod_template = assertions.Template.from_stack(prod_stack)
    
    prod_template.has_resource_properties("AWS::Lambda::Url", {
        "Cors": {
            "AllowOrigins": ["https://daily-checkin.example.com"]
        }
    })

def test_lambda_versioning_production_environment():
    """本番環境でのLambda関数バージョニング設定をテスト"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="prod", project_name="test-project")
    template = assertions.Template.from_stack(stack)
    
    # Lambda関数のエイリアスが作成されることを確認
    template.resource_count_is("AWS::Lambda::Alias", 2)
    
    # LIVE エイリアスの設定を確認
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "LIVE",
        "Description": "本番環境用のLambda関数エイリアス"
    })
    
    # STAGING エイリアスの設定を確認
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "STAGING", 
        "Description": "ステージング環境用のLambda関数エイリアス"
    })
    
    # エイリアスARNの出力を確認
    template.has_output("LambdaLiveAliasArn", {
        "Description": "Lambda function LIVE alias ARN"
    })
    
    template.has_output("LambdaStagingAliasArn", {
        "Description": "Lambda function STAGING alias ARN"
    })


def test_lambda_versioning_development_environment():
    """開発環境でのLambda関数バージョニング設定をテスト（バージョニング無効）"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="dev", project_name="test-project")
    template = assertions.Template.from_stack(stack)
    
    # 開発環境ではエイリアスが作成されないことを確認
    template.resource_count_is("AWS::Lambda::Alias", 0)


def test_lambda_versioning_comprehensive():
    """Lambda関数バージョニングの包括的テスト - エイリアス設定、出力、統合を統合"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="prod", project_name="test-project")
    template = assertions.Template.from_stack(stack)
    
    # Lambda関数のエイリアスが作成されることを確認
    template.resource_count_is("AWS::Lambda::Alias", 2)
    
    # LIVE エイリアスの設定を確認
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "LIVE",
        "Description": "本番環境用のLambda関数エイリアス"
    })
    
    # STAGING エイリアスの設定を確認
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "STAGING", 
        "Description": "ステージング環境用のLambda関数エイリアス"
    })
    
    # エイリアスARNの出力を確認
    template.has_output("LambdaLiveAliasArn", {
        "Description": "Lambda function LIVE alias ARN",
        "Export": {
            "Name": "test-project-prod-lambda-live-alias-arn"
        }
    })
    
    template.has_output("LambdaStagingAliasArn", {
        "Description": "Lambda function STAGING alias ARN",
        "Export": {
            "Name": "test-project-prod-lambda-staging-alias-arn"
        }
    })
    
    # Lambda関数とバージョニングの統合確認
    template.resource_count_is("AWS::Lambda::Function", 2)  # バージョニングにより複数作成
    template.resource_count_is("AWS::Lambda::Url", 1)       # Function URL


def test_environment_specific_versioning_behavior():
    """環境固有のバージョニング動作をテスト - 全環境での動作確認"""
    # ローカル環境でのテスト
    local_app = core.App()
    local_stack = DailyCheckinStack(local_app, "local-stack", environment="local", project_name="test-project")
    local_template = assertions.Template.from_stack(local_stack)
    
    # ローカル環境ではエイリアスが作成されないことを確認
    local_template.resource_count_is("AWS::Lambda::Alias", 0)
    
    # ステージング環境でのテスト
    staging_app = core.App()
    staging_stack = DailyCheckinStack(staging_app, "staging-stack", environment="staging", project_name="test-project")
    staging_template = assertions.Template.from_stack(staging_stack)
    
    # ステージング環境ではエイリアスが作成されることを確認
    staging_template.resource_count_is("AWS::Lambda::Alias", 2)
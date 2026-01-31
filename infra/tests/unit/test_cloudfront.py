import aws_cdk as core
import aws_cdk.assertions as assertions
from infra.infra_stack import DailyCheckinStack

def test_cloudfront_distribution_created():
    """CloudFrontディストリビューションが正しく作成されることをテスト"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test")
    template = assertions.Template.from_stack(stack)

    # 要件 2.1: S3バケットを指すCloudFrontディストリビューションを作成
    template.resource_count_is("AWS::CloudFront::Distribution", 1)

def test_cloudfront_https_redirect():
    """
    Verifies the CloudFront Distribution enforces HTTPS by using the `redirect-to-https` viewer protocol policy.
    """
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test")
    template = assertions.Template.from_stack(stack)

    # 要件 2.2: デフォルトでHTTPS有効でコンテンツを配信
    template.has_resource_properties("AWS::CloudFront::Distribution", {
        "DistributionConfig": {
            "DefaultCacheBehavior": {
                "ViewerProtocolPolicy": "redirect-to-https"
            }
        }
    })

def test_cloudfront_default_root_object():
    """
    Check that the CloudFront distribution's default root object is set to "index.html".
    
    Asserts that the synthesized CloudFormation template contains an AWS::CloudFront::Distribution
    resource whose DistributionConfig.DefaultRootObject equals "index.html".
    """
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test")
    template = assertions.Template.from_stack(stack)

    # 要件 2.4: デフォルトルートオブジェクトを"index.html"として設定
    template.has_resource_properties("AWS::CloudFront::Distribution", {
        "DistributionConfig": {
            "DefaultRootObject": "index.html"
        }
    })

def test_origin_access_identity_created():
    """
    Verifies that a CloudFront Origin Access Identity resource is created in the synthesized CloudFormation template.
    
    Asserts that exactly one AWS::CloudFront::CloudFrontOriginAccessIdentity resource is present in the stack.
    """
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test")
    template = assertions.Template.from_stack(stack)

    # OAIの作成確認
    template.resource_count_is("AWS::CloudFront::CloudFrontOriginAccessIdentity", 1)
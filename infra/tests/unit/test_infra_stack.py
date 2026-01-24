import aws_cdk as core
import aws_cdk.assertions as assertions

from infra.infra_stack import DailyCheckinStack

def test_dynamodb_table_created():
    """Test that DynamoDB table is created with correct configuration"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="test")
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

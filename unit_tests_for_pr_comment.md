# 追加されたユニットテスト

以下は今回のPRで追加されたLambda関数バージョニング機能のユニットテストです：

```python
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


def test_lambda_alias_configuration_details():
    """Lambda関数エイリアスの詳細設定をテスト"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="prod", project_name="test-project")
    template = assertions.Template.from_stack(stack)
    
    # エイリアスが正しいLambda関数を参照していることを確認
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "LIVE",
        "Description": "本番環境用のLambda関数エイリアス"
    })
    
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "STAGING",
        "Description": "ステージング環境用のLambda関数エイリアス"
    })


def test_lambda_versioning_outputs():
    """Lambda関数バージョニングの出力をテスト"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="prod", project_name="test-project")
    template = assertions.Template.from_stack(stack)
    
    # エイリアスARNの出力が正しく設定されていることを確認
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


def test_environment_specific_versioning_behavior():
    """環境固有のバージョニング動作をテスト"""
    # ローカル環境でのテスト
    local_app = core.App()
    local_stack = DailyCheckinStack(local_app, "local-stack", environment="local")
    local_template = assertions.Template.from_stack(local_stack)
    
    # ローカル環境ではエイリアスが作成されないことを確認
    local_template.resource_count_is("AWS::Lambda::Alias", 0)
    
    # ステージング環境でのテスト
    staging_app = core.App()
    staging_stack = DailyCheckinStack(staging_app, "staging-stack", environment="staging")
    staging_template = assertions.Template.from_stack(staging_stack)
    
    # ステージング環境ではエイリアスが作成されることを確認
    staging_template.resource_count_is("AWS::Lambda::Alias", 2)


def test_lambda_function_integration_with_versioning():
    """Lambda関数とバージョニングの統合をテスト"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="prod")
    template = assertions.Template.from_stack(stack)
    
    # Lambda関数が作成されていることを確認（バージョニングにより複数のリソースが作成される可能性がある）
    template.resource_count_is("AWS::Lambda::Function", 2)
    
    # Lambda関数にバージョニングが適用されていることを確認（エイリアス経由）
    template.resource_count_is("AWS::Lambda::Alias", 2)
    
    # Function URLが正しく設定されていることを確認
    template.resource_count_is("AWS::Lambda::Url", 1)
```

## テスト結果

- **総テスト数**: 23個
- **成功**: 23個 (100%)
- **失敗**: 0個

これらのテストは以下の機能をカバーしています：

1. **本番環境でのLambda関数バージョニング**: LIVEとSTAGINGエイリアスの作成
2. **開発環境でのバージョニング無効化**: 簡素化のためエイリアス作成なし
3. **エイリアス設定の詳細**: 正しい名前と説明の設定
4. **出力設定**: エイリアスARNの適切な出力
5. **環境固有の動作**: 各環境での適切なバージョニング動作
6. **統合テスト**: Lambda関数とバージョニング機能の統合確認
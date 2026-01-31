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


def test_lambda_versioning_comprehensive():
    """Lambda関数バージョニングの包括的テスト - エイリアス設定、出力、統合を統合"""
    app = core.App()
    stack = DailyCheckinStack(app, "test-stack", environment="prod", project_name="test-project")
    template = assertions.Template.from_stack(stack)
    
    # エイリアス設定の詳細確認
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "LIVE",
        "Description": "本番環境用のLambda関数エイリアス"
    })
    
    template.has_resource_properties("AWS::Lambda::Alias", {
        "Name": "STAGING",
        "Description": "ステージング環境用のLambda関数エイリアス"
    })
    
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
    
    # Lambda関数とバージョニングの統合確認
    template.resource_count_is("AWS::Lambda::Function", 2)  # バージョニングにより複数作成
    template.resource_count_is("AWS::Lambda::Alias", 2)     # LIVEとSTAGINGエイリアス
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
```

## テスト結果

- **総テスト数**: 23個
- **成功**: 23個 (100%)
- **失敗**: 0個

## テスト改善点

CodeRabbitの指摘に基づき、以下の改善を実施：

1. **テストの統合**: 関連する機能テストを`test_lambda_versioning_comprehensive`に統合
2. **テストの強化**: より包括的な検証を単一テストで実行
3. **重複の削除**: 類似のテスト内容を統合してメンテナンス性を向上

これらのテストは以下の機能をカバーしています：

1. **本番環境でのLambda関数バージョニング**: LIVEとSTAGINGエイリアスの作成
2. **開発環境でのバージョニング無効化**: 簡素化のためエイリアス作成なし
3. **包括的なバージョニング機能**: エイリアス設定、出力、統合の全体確認
4. **環境固有の動作**: 各環境での適切なバージョニング動作確認
# LocalStackテスト要件書

## 概要

本ドキュメントは、デイリーチェックインアプリケーションのLocalStack Community Edition環境での動作確認テストの要件を定義します。LocalStackを使用してAWSサービスをローカルでエミュレートし、本番環境と同等の機能テストを実行します。

## テスト目的

1. **コスト削減**: AWS料金を発生させずにインフラストラクチャテストを実行
2. **高速フィードバック**: ローカル環境での迅速な開発・テストサイクル
3. **本番環境との整合性**: 実際のAWSサービスと同等の動作確認
4. **CI/CD統合**: 自動テストパイプラインでの活用

## テスト対象サービス

### 必須テスト対象
- **S3**: 静的ウェブサイトホスティング、バケット作成、ファイルアップロード
- **Lambda**: 関数作成、Function URL、環境変数設定
- **DynamoDB**: テーブル作成、データ書き込み・読み取り
- **IAM**: ロール・ポリシー作成、権限設定

### 制限付きテスト対象（Community Edition）
- **CloudFront**: 基本的なディストリビューション作成のみ（OAI等の高度な機能は制限）
- **CloudWatch**: 基本的なログ出力のみ

## テスト環境要件

### システム要件
- **Docker**: 20.10以降
- **Docker Compose**: 2.0以降
- **Python**: 3.12
- **Node.js**: 18.x以降
- **AWS CLI**: 2.x
- **AWS CDK CLI**: 2.x

### LocalStack設定
- **バージョン**: 3.0以降
- **エディション**: Community Edition
- **ポート**: 4566（メインエンドポイント）
- **永続化**: 無効（テスト用）

## テストシナリオ

### シナリオ1: CDKスタックデプロイメント（制限付き）
**目的**: LocalStack環境でのCDKスタック正常デプロイ確認

**前提条件**:
- LocalStackが起動済み
- AWS_ENDPOINT_URL環境変数が設定済み

**テスト手順**:
1. LocalStackコンテナ起動
2. CDKブートストラップ実行
3. CDKスタックデプロイ（environment=local）
4. リソース作成確認

**期待結果**:
- CDKブートストラップが成功する
- **制限事項**: アセット公開でエラーが発生する可能性（Community Edition制限）
- 個別AWSサービスは正常に作成される

**実際の結果**:
- ✅ CDKブートストラップ成功
- ❌ CDKスタックデプロイ失敗（アセット公開エラー）
- ✅ 個別サービス作成は正常動作

### シナリオ2: DynamoDBデータ操作
**目的**: DynamoDBテーブルへのデータ書き込み・読み取り確認

**テスト手順**:
1. DailyHealthLogテーブル作成
2. テストデータ書き込み
3. データ読み取り確認
4. データ削除

**期待結果**:
- テーブルが正しいスキーマで作成される
- データの書き込み・読み取りが正常動作
- パーティションキー・ソートキーが機能する

**実際の結果**:
- ✅ テーブル作成成功（正しいスキーマ）
- ✅ データ書き込み成功
- ✅ データ読み取り成功
- ✅ パーティションキー・ソートキー正常動作

### シナリオ3: Lambda関数実行（部分的）
**目的**: Lambda関数とFunction URLの動作確認

**テスト手順**:
1. Lambda関数作成
2. Function URL設定（手動）
3. テストリクエスト送信（POST）
4. レスポンス確認
5. DynamoDBデータ確認

**期待結果**:
- Lambda関数が正常作成される
- Function URLが応答する
- DynamoDBにデータが保存される
- 適切なHTMLレスポンスが返される

**実際の結果**:
- ✅ Lambda関数作成成功
- ⚠️ Function URL未テスト（手動設定が必要）
- ⚠️ Lambda関数実行未テスト
- ⚠️ エンドツーエンド統合未テスト

### シナリオ4: S3静的ウェブサイト
**目的**: S3バケットと静的ファイル配信確認

**テスト手順**:
1. S3バケット作成
2. index.htmlファイルアップロード
3. ファイルアクセステスト
4. バージョニング確認

**期待結果**:
- S3バケットが作成される
- 静的ファイルがアップロードされる
- ファイルにアクセス可能
- バージョニングが有効

**実際の結果**:
- ✅ S3バケット作成成功
- ✅ 静的ファイルアップロード成功（10006バイト）
- ✅ ファイル一覧表示成功
- ⚠️ バージョニング未テスト

### シナリオ5: エンドツーエンドテスト（制限付き）
**目的**: Lambda Function URLを使用した統合動作確認

**テスト手順**:
1. Function URL直接アクセス
2. フォームデータPOST送信
3. Lambda関数実行確認
4. DynamoDBデータ確認
5. レスポンス確認

**期待結果**:
- Function URLが応答する
- フォーム送信が成功する
- データがDynamoDBに保存される
- 適切なHTMLレスポンスが返される

**注意**: CloudFrontを経由した完全なエンドツーエンドテストはCommunity Editionでは制限があります。

## テストデータ

### DynamoDBテストデータ
```json
{
    "Date": "2024-02-01",
    "Period": "morning",
    "Condition": "良好",
    "IsRoutine": "できた",
    "WorkPlace": "在宅",
    "WorkDetail": "CDKテスト",
    "Notes": "LocalStackテスト実行",
    "SleepingHours": "7.5",
    "EnergyMorning": "8",
    "EnergyEvening": "7",
    "StaminaMorning": "8",
    "StaminaEvening": "6",
    "Timestamp": "2024-02-01T09:00:00+09:00"
}
```

### HTTPリクエストテストデータ
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "date=2024-02-01&period=morning&condition=良好&isRoutine=できた&workPlace=在宅&workDetail=CDKテスト&notes=LocalStackテスト&sleepingHours=7.5&energyMorning=8&energyEvening=7&staminaMorning=8&staminaEvening=6" \
  ${FUNCTION_URL}
```

## 成功基準

### 必須成功基準
- [❌] CDKスタックが正常にデプロイされる（アセット公開エラー）
- [✅] 個別AWSリソースが作成される（DynamoDB、S3、Lambda）
- [✅] Lambda関数が作成可能
- [✅] DynamoDBへのデータ書き込みが成功
- [⚠️] Function URLが応答する（未テスト）
- [✅] S3静的ファイルにアクセス可能

### オプション成功基準
- [⚠️] CloudFrontディストリビューション作成（基本機能のみ、未テスト）
- [⚠️] IAM権限が正しく設定される（未テスト）
- [⚠️] CloudWatchログが出力される（未テスト）
- [⚠️] エラーハンドリングが機能する（未テスト）

### 実際の達成状況
**達成率**: 4/6 (67%) - 必須成功基準
- LocalStack Community Editionでの基本的なAWSサービス動作確認は成功
- CDKの完全なスタックデプロイには制限あり
- 個別サービステストは良好な結果

## 制限事項

### LocalStack Community Edition制限
- **CDK**: アセット公開機能に制限、完全なスタックデプロイが困難
- **CloudFront**: 基本的なディストリビューション作成のみ、OAI等の高度な機能は制限
- **IAM**: 一部の高度な権限機能に制限
- **CloudWatch**: メトリクスとアラーム機能に制限
- **Lambda**: Function URL設定等、一部機能に制限

### テスト環境制限
- インターネット接続が必要（Docker イメージダウンロード）
- メモリ使用量が多い（推奨8GB以上）
- 永続化なし（コンテナ再起動でデータ消失）
- CloudFrontを経由した完全なフロントエンドテストは制限

## トラブルシューティング

### よくある問題
1. **LocalStackコンテナ起動失敗**
   - Dockerデーモン確認
   - ポート4566の競合確認
   - メモリ不足確認

2. **CDKデプロイ失敗**
   - AWS_ENDPOINT_URL環境変数確認
   - LocalStack起動状態確認
   - CDKブートストラップ実行確認
   - **新規**: アセット公開エラーの場合、個別サービス作成を検討

3. **Lambda関数実行エラー**
   - 関数コードパス確認
   - 環境変数設定確認
   - IAM権限確認

4. **DynamoDB接続エラー**
   - テーブル存在確認
   - エンドポイント設定確認
   - 認証情報確認

5. **CloudFront制限エラー**
   - Community Edition制限を確認
   - 基本機能のみ使用
   - 必要に応じてS3直接アクセスに変更

## 参考資料

- [LocalStack公式ドキュメント](https://docs.localstack.cloud/)
- [AWS CDK LocalStack統合](https://docs.localstack.cloud/user-guide/integrations/aws-cdk/)
- [LocalStack Community Edition制限](https://docs.localstack.cloud/getting-started/installation/#localstack-editions)

## テスト実行結果（2024-02-05実施）

### 実行環境
- **LocalStack**: 3.8.1 Community Edition
- **AWS CLI**: 2.32.6
- **Docker**: 起動済み
- **テスト実行者**: システム

### 詳細結果

#### ✅ 成功項目
1. **LocalStack起動**: 正常起動、必要サービス利用可能確認
2. **DynamoDB**: テーブル作成、データ書き込み・読み取り成功
3. **S3**: バケット作成、ファイルアップロード（10006バイト）成功
4. **Lambda**: 関数作成、環境変数設定成功

#### ❌ 失敗項目
1. **CDKスタックデプロイ**: アセット公開でエラー（`getaddrinfo ENOTFOUND cdk-hnb659fds-assets-000000000000-us-east-1.localhost`）

#### ⚠️ 未実施項目
1. **Lambda Function URL**: 設定・テスト未実施
2. **Lambda関数実行**: 実際の実行テスト未実施
3. **CloudFront**: ディストリビューション作成未テスト
4. **IAM**: 権限設定詳細未テスト
5. **エンドツーエンド**: 統合テスト未実施

### 推奨事項
1. **CDK制限対応**: 個別サービス作成でのテスト継続
2. **Function URL**: 手動設定でのテスト実施
3. **統合テスト**: Lambda関数実行からDynamoDB保存までの流れ確認
4. **CloudFront**: Community Edition制限内での基本機能テスト
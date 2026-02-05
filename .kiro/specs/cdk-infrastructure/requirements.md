# 要件定義書

## はじめに

この文書は、既存のサーバーレスデイリーチェックインアプリケーションをAWS CDKでIaC（Infrastructure as Code）化するための要件を定義します。現在手動でデプロイされているS3/CloudFront静的サイト、Lambda関数、DynamoDBをCDKコードで管理可能にし、AWS公式のベストプラクティスに準拠した安全で再現可能なデプロイメントを実現します。

本要件は、AWS Well-Architected Framework の5つの柱（運用性、セキュリティ、信頼性、パフォーマンス、コスト最適化）に基づいて策定されています。

## 用語集

- **CDK_Stack**: すべてのAWSリソースを定義するAWS CDKインフラストラクチャスタック
- **Static_Website**: CloudFront経由で配信されるS3ホスト型のHTML/CSS/JSファイル
- **Lambda_Function**: フォーム送信を処理してデータを保存するPython関数
- **DynamoDB_Table**: デイリーチェックイン記録を保存するNoSQLデータベーステーブル
- **CloudFront_Distribution**: 静的コンテンツをグローバルに配信するCDN
- **Function_URL**: API Gatewayを使わずに直接HTTPアクセスするためのAWS Lambda Function URL
- **LocalStack**: ローカル開発環境でAWSサービスをエミュレートするツール
- **Fine-grained_Assertions**: CDKリソースの特定プロパティを検証するテスト手法
- **cdk-nag**: CDKコードのセキュリティ・コンプライアンス自動検証ツール
- **OAC**: Origin Access Control - CloudFrontからS3への安全なアクセス制御（OAIの後継）
- **Generated_Names**: CDKが自動生成するリソース名（物理名の指定を避けるベストプラクティス）

## 要件

### 要件1: 既存S3静的ウェブサイトのCDK化（セキュリティ強化）

**ユーザーストーリー:** 開発者として、既存の手動デプロイされたS3静的ウェブサイトをCDKで管理したい。そうすることで、インフラストラクチャをコードとして管理し、セキュリティベストプラクティスに準拠した再現可能なデプロイメントを実現できる。

#### 受入基準

1. THE CDK_Stack SHALL 既存のS3バケット設定と同等の静的ウェブサイトホスティング用バケットを作成する
2. THE CDK_Stack SHALL 既存のS3/index.htmlファイルを新しいバケットにデプロイする機能を提供する
3. THE S3_Bucket SHALL パブリックアクセスブロック設定を有効にし、CloudFrontからのアクセスのみを許可する
4. THE S3_Bucket SHALL デプロイロールバック機能のためにバージョニングを有効にする
5. THE S3_Bucket SHALL 保存時暗号化（AES-256またはKMS）を有効にする
6. THE S3_Bucket SHALL Generated_Namesを使用し、物理名の指定を避ける（CDKベストプラクティス）

### 要件2: 既存CloudFrontディストリビューションのCDK化（セキュリティヘッダー強化）

**ユーザーストーリー:** 開発者として、既存のCloudFrontディストリビューションをCDKで管理したい。そうすることで、CDN設定をコードとして管理し、セキュリティヘッダーを含む一貫性のあるデプロイメントを実現できる。

#### 受入基準

1. THE CDK_Stack SHALL S3バケットを指すCloudFrontディストリビューションを作成する
2. THE CloudFront_Distribution SHALL HTTPS強制（HTTP→HTTPSリダイレクト）でコンテンツを配信する
3. THE CloudFront_Distribution SHALL セキュリティヘッダー（HSTS、X-Frame-Options等）を設定する
4. THE CloudFront_Distribution SHALL デフォルトルートオブジェクトを"index.html"として設定する
5. THE CloudFront_Distribution SHALL Origin Access Control（OAC）を使用してS3への安全なアクセスを実現する
6. THE CloudFront_Distribution SHALL 適切なキャッシュポリシーで静的アセットを最適化する
7. WHEN ユーザーがCloudFront URLにアクセスした時、THE CloudFront_Distribution SHALL 1秒以内のTTFBで静的ウェブサイトを配信する

### 要件3: 既存Lambda関数のCDK化（パフォーマンス・セキュリティ強化）

**ユーザーストーリー:** 開発者として、既存のLambda関数（lamda/submit_daily_checkin.py）をCDKで管理したい。そうすることで、関数のデプロイメントとバージョン管理をコードで自動化し、パフォーマンスとセキュリティを向上できる。

#### 受入基準

1. THE CDK_Stack SHALL 既存のlamda/submit_daily_checkin.pyファイルを使用してLambda関数を作成する
2. THE Lambda_Function SHALL Python 3.12以降の最新安定版ランタイムで設定される
3. THE Lambda_Function SHALL 既存のDynamoDBテーブル"DailyHealthLog"への書き込みに適切なIAM権限を持つ
4. THE Lambda_Function SHALL DynamoDBテーブル名用の環境変数を設定する
5. THE Lambda_Function SHALL 200ms以内のレスポンス時間を実現するために適切なメモリ設定を持つ
6. THE Lambda_Function SHALL デッドレターキュー（DLQ）を設定してエラーハンドリングを強化する
7. THE Lambda_Function SHALL CloudWatchログへの構造化ログ出力を設定する

### 要件4: Lambda Function URL設定（セキュリティ・パフォーマンス強化）

**ユーザーストーリー:** フロントエンドアプリケーションとして、Lambdaに直接フォームデータを送信したい。そうすることで、このシンプルなユースケースでAPI Gatewayの複雑さを避け、低レイテンシーでセキュアなアクセスを実現できる。

#### 受入基準

1. THE CDK_Stack SHALL 直接HTTPアクセス用のLambda Function URLを作成する
2. THE Function_URL SHALL フロントエンドアプリケーションからのPOSTリクエストを受け入れる
3. THE Function_URL SHALL 適切なCORS設定で特定ドメインからのアクセスのみを許可する
4. THE Function_URL SHALL パブリックアクセス用にNONE認証タイプを使用する
5. THE Function_URL SHALL レート制限とDDoS保護のための適切な設定を持つ
6. WHEN フロントエンドがフォームを送信した時、THE Function_URL SHALL 200ms以内でリクエストをLambda関数にルーティングする

### 要件5: 既存DynamoDBテーブルのCDK化（セキュリティ・バックアップ強化）

**ユーザーストーリー:** 開発者として、既存のDynamoDBテーブル"DailyHealthLog"をCDKで管理したい。そうすることで、データベーススキーマとアクセス権限をコードとして管理し、データ保護を強化できる。

#### 受入基準

1. THE CDK_Stack SHALL 既存の"DailyHealthLog"テーブルと同じスキーマでDynamoDBテーブルを作成する
2. THE DynamoDB_Table SHALL 既存と同様にパーティションキーとして"Date"を持つ（文字列型）
3. THE DynamoDB_Table SHALL 既存と同様にソートキーとして"Period"を持つ（文字列型）
4. THE DynamoDB_Table SHALL コスト最適化のためにオンデマンド課金モードを使用する
5. THE DynamoDB_Table SHALL データ保護のためにポイントインタイムリカバリを有効にする
6. THE DynamoDB_Table SHALL 保存時暗号化（AWS管理キーまたはカスタマー管理キー）を有効にする
7. THE DynamoDB_Table SHALL Generated_Namesを使用し、物理テーブル名の指定を避ける

### 要件6: IAMセキュリティ設定（最小権限の原則強化）

**ユーザーストーリー:** セキュリティ意識の高い開発者として、適切なIAM権限を設定したい。そうすることで、リソースが最小限の必要なアクセス権を持ち、最小権限の原則に従い、cdk-nagによる自動検証に合格する。

#### 受入基準

1. THE Lambda_Function SHALL 最小限の必要な権限を持つIAMロールを持つ
2. THE Lambda_Function SHALL DynamoDBテーブルへのアイテム書き込み権限のみを持つ（読み取り権限なし）
3. THE Lambda_Function SHALL CloudWatchへのログ書き込み権限を持つ
4. THE S3_Bucket SHALL CloudFrontアクセスのみを許可するバケットポリシーを持つ
5. THE CDK_Stack SHALL 過度に許可的なIAMポリシー（ワイルドカード権限）を作成してはならない
6. THE CDK_Stack SHALL cdk-nagによるIAMセキュリティルール検証に100%合格する
7. THE IAM_Roles SHALL リソースベースポリシーで特定リソースへのアクセスのみを許可する

### 要件7: 環境設定（AWS Well-Architected Framework準拠）

**ユーザーストーリー:** 開発者として、環境固有の設定が欲しい。そうすることで、同じCDKコードを異なる環境（dev、staging、prod）にデプロイでき、AWS Well-Architected Frameworkの運用性の柱に準拠できる。

#### 受入基準

1. THE CDK_Stack SHALL Generated_Namesを使用し、環境パラメータによる命名規則を適用する
2. THE CDK_Stack SHALL すべてのリソースで一貫した命名規則を使用する
3. THE CDK_Stack SHALL すべてのリソースに環境、プロジェクト、コスト管理用のタグを設定する
4. THE Lambda_Function SHALL 環境変数経由でDynamoDBテーブル名を受け取る
5. THE CDK_Stack SHALL 重要なリソース識別子（CloudFront URL、Function URL）を出力する
6. THE CDK_Stack SHALL cdk.context.jsonを適切に管理し、非決定的動作を回避する
7. THE CDK_Stack SHALL 環境ごとの設定差分を最小化し、設定ドリフトを防止する

### 要件8: デプロイメントとロールバックサポート（学習重点）

**ユーザーストーリー:** 開発者として、CDKの基本的なデプロイメントとロールバック機能を理解したい。そうすることで、安全にインフラストラクチャ変更を管理する方法を学習できる。

#### 受入基準

1. THE CDK_Stack SHALL 基本的な増分デプロイメントをサポートする
2. THE S3_Bucket SHALL バージョニングを有効にする
3. THE Lambda_Function SHALL 基本的なバージョニングをサポートする
4. THE CDK_Stack SHALL デプロイメント前にリソース依存関係を検証する
5. WHEN デプロイメントが失敗した時、THE CDK_Stack SHALL 明確なエラーメッセージを提供する

### 要件9: ローカル開発環境サポート（LocalStack統合強化）

**ユーザーストーリー:** 開発者として、ローカル環境でAWSサービスをエミュレートしたい。そうすることで、AWS料金を気にせずに開発・テストを行い、高速なフィードバックループを実現し、CI/CDパイプラインに統合できる。

#### 受入基準

1. THE CDK_Stack SHALL LocalStack Community Edition環境での動作をサポートする
2. WHEN 環境パラメータが"local"の時、THE CDK_Stack SHALL LocalStackエンドポイントを使用する
3. THE CDK_Stack SHALL LocalStack用のDocker Compose設定を提供する
4. THE CDK_Stack SHALL ローカル環境と実AWS環境で同一のリソース構成を維持する
5. THE CDK_Stack SHALL LocalStack環境でのFine-grained assertionsテスト実行をサポートする
6. THE CDK_Stack SHALL LocalStack Community Edition制限事項を文書化し、回避策を提供する
7. THE CDK_Stack SHALL CI/CDパイプラインでのLocalStackテスト自動実行をサポートする

### 要件10: テスト・品質保証（学習重点）

**ユーザーストーリー:** 開発者として、CDKインフラストラクチャテストの基本を学習したい。そうすることで、インフラストラクチャコードの品質を保証する方法を理解できる。

#### 受入基準

1. THE CDK_Stack SHALL Fine-grained assertionsテストで主要リソースプロパティを検証する
2. THE CDK_Stack SHALL AWS CDK Assertionsモジュールを使用したテストスイートを提供する
3. THE CDK_Stack SHALL cdk-nagによる基本的なセキュリティ検証を実行する
4. THE CDK_Stack SHALL LocalStack環境でのテスト実行をサポートする
5. THE CDK_Stack SHALL テスト実行の基本的なレポート機能を提供する

### 要件11: 基本的な監視設定（学習重点）

**ユーザーストーリー:** 開発者として、AWSリソースの基本的な監視方法を学習したい。そうすることで、システムの動作状況を把握し、問題の早期発見方法を理解できる。

#### 受入基準

1. THE Lambda_Function SHALL CloudWatchログ出力を設定する
2. THE CDK_Stack SHALL 基本的なCloudWatchメトリクス監視を設定する
3. THE CDK_Stack SHALL コスト追跡用のタグ設定を実装する
4. THE CDK_Stack SHALL 基本的なアラーム設定（Lambda エラー率）を提供する
5. THE CDK_Stack SHALL ログ確認とトラブルシューティングの基本手順を文書化する
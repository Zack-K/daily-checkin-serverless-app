# 要件定義書

## はじめに

この文書は、既存のサーバーレスデイリーチェックインアプリケーションをAWS CDKでIaC（Infrastructure as Code）化するための要件を定義します。現在手動でデプロイされているS3/CloudFront静的サイト、Lambda関数、DynamoDBをCDKコードで管理可能にし、再現可能なデプロイメントを実現します。

## 用語集

- **CDK_Stack**: すべてのAWSリソースを定義するAWS CDKインフラストラクチャスタック
- **Static_Website**: CloudFront経由で配信されるS3ホスト型のHTML/CSS/JSファイル
- **Lambda_Function**: フォーム送信を処理してデータを保存するPython関数
- **DynamoDB_Table**: デイリーチェックイン記録を保存するNoSQLデータベーステーブル
- **CloudFront_Distribution**: 静的コンテンツをグローバルに配信するCDN
- **Function_URL**: API Gatewayを使わずに直接HTTPアクセスするためのAWS Lambda Function URL
- **LocalStack**: ローカル開発環境でAWSサービスをエミュレートするツール

## 要件

### 要件1: 既存S3静的ウェブサイトのCDK化

**ユーザーストーリー:** 開発者として、既存の手動デプロイされたS3静的ウェブサイトをCDKで管理したい。そうすることで、インフラストラクチャをコードとして管理し、再現可能なデプロイメントを実現できる。

#### 受入基準

1. THE CDK_Stack SHALL 既存のS3バケット設定と同等の静的ウェブサイトホスティング用バケットを作成する
2. THE CDK_Stack SHALL 既存のS3/index.htmlファイルを新しいバケットにデプロイする機能を提供する
3. THE S3_Bucket SHALL ウェブサイトホスティングに適切なパブリック読み取り権限を設定する
4. THE S3_Bucket SHALL デプロイロールバック機能のためにバージョニングを有効にする
5. THE S3_Bucket SHALL セキュリティベストプラクティスに従ってアクセス制御を設定する

### 要件2: 既存CloudFrontディストリビューションのCDK化

**ユーザーストーリー:** 開発者として、既存のCloudFrontディストリビューションをCDKで管理したい。そうすることで、CDN設定をコードとして管理し、一貫性のあるデプロイメントを実現できる。

#### 受入基準

1. THE CDK_Stack SHALL S3バケットを指すCloudFrontディストリビューションを作成する
2. THE CloudFront_Distribution SHALL デフォルトでHTTPS有効でコンテンツを配信する
3. THE CloudFront_Distribution SHALL 適切なTTL設定で静的アセットをキャッシュする
4. THE CloudFront_Distribution SHALL デフォルトルートオブジェクトを"index.html"として設定する
5. WHEN ユーザーがCloudFront URLにアクセスした時、THE CloudFront_Distribution SHALL 静的ウェブサイトを配信する

### 要件3: 既存Lambda関数のCDK化

**ユーザーストーリー:** 開発者として、既存のLambda関数（lamda/submit_daily_checkin.py）をCDKで管理したい。そうすることで、関数のデプロイメントとバージョン管理をコードで自動化できる。

#### 受入基準

1. THE CDK_Stack SHALL 既存のlamda/submit_daily_checkin.pyファイルを使用してLambda関数を作成する
2. THE Lambda_Function SHALL 既存コードと互換性のあるPython 3.9以降のランタイムで設定される
3. THE Lambda_Function SHALL 既存のDynamoDBテーブル"DailyHealthLog"への書き込みに適切なIAM権限を持つ
4. THE Lambda_Function SHALL DynamoDBテーブル名用の環境変数を設定する
5. THE Lambda_Function SHALL 既存の処理要件に対応するために少なくとも30秒のタイムアウトを持つ

### 要件4: Lambda Function URL設定

**ユーザーストーリー:** フロントエンドアプリケーションとして、Lambdaに直接フォームデータを送信したい。そうすることで、このシンプルなユースケースでAPI Gatewayの複雑さを避けられる。

#### 受入基準

1. THE CDK_Stack SHALL 直接HTTPアクセス用のLambda Function URLを作成する
2. THE Function_URL SHALL フロントエンドアプリケーションからのPOSTリクエストを受け入れる
3. THE Function_URL SHALL CloudFrontドメインからのリクエストを許可するCORSを設定する
4. THE Function_URL SHALL パブリックアクセス用にNONE認証タイプを使用する
5. WHEN フロントエンドがフォームを送信した時、THE Function_URL SHALL リクエストをLambda関数にルーティングする

### 要件5: 既存DynamoDBテーブルのCDK化

**ユーザーストーリー:** 開発者として、既存のDynamoDBテーブル"DailyHealthLog"をCDKで管理したい。そうすることで、データベーススキーマとアクセス権限をコードとして管理できる。

#### 受入基準

1. THE CDK_Stack SHALL 既存の"DailyHealthLog"テーブルと同じスキーマでDynamoDBテーブルを作成する
2. THE DynamoDB_Table SHALL 既存と同様にパーティションキーとして"Date"を持つ（文字列型）
3. THE DynamoDB_Table SHALL 既存と同様にソートキーとして"Period"を持つ（文字列型）
4. THE DynamoDB_Table SHALL コスト最適化のためにオンデマンド課金モードを使用する
5. THE DynamoDB_Table SHALL データ保護のためにポイントインタイムリカバリを有効にする

### 要件6: IAMセキュリティ設定

**ユーザーストーリー:** セキュリティ意識の高い開発者として、適切なIAM権限を設定したい。そうすることで、リソースが最小限の必要なアクセス権を持ち、最小権限の原則に従う。

#### 受入基準

1. THE Lambda_Function SHALL 最小限の必要な権限を持つIAMロールを持つ
2. THE Lambda_Function SHALL DynamoDBテーブルへのアイテム書き込み権限のみを持つ
3. THE Lambda_Function SHALL CloudWatchへのログ書き込み権限を持つ
4. THE S3_Bucket SHALL CloudFrontアクセスのみを許可するバケットポリシーを持つ
5. THE CDK_Stack SHALL 過度に許可的なIAMポリシーを作成してはならない

### 要件7: 環境設定

**ユーザーストーリー:** 開発者として、環境固有の設定が欲しい。そうすることで、同じCDKコードを異なる環境（dev、staging、prod）にデプロイできる。

#### 受入基準

1. THE CDK_Stack SHALL リソース命名用の環境パラメータを受け入れる
2. THE CDK_Stack SHALL すべてのリソースで一貫した命名規則を使用する
3. THE CDK_Stack SHALL すべてのリソースに環境とプロジェクト識別子でタグ付けする
4. THE Lambda_Function SHALL 環境変数経由でDynamoDBテーブル名を受け取る
5. THE CDK_Stack SHALL 重要なリソース識別子（CloudFront URL、Function URL）を出力する

### 要件8: デプロイメントとロールバックサポート

**ユーザーストーリー:** 開発者として、信頼性の高いデプロイメントとロールバック機能が欲しい。そうすることで、安全に変更をデプロイし、問題が発生した場合に元に戻せる。

#### 受入基準

1. THE CDK_Stack SHALL ダウンタイムなしの増分デプロイメントをサポートする
2. THE S3_Bucket SHALL 静的アセットの以前のバージョンを維持する
3. THE Lambda_Function SHALL ロールバック機能のためにバージョニングをサポートする
4. THE CDK_Stack SHALL デプロイメント前にすべてのリソース依存関係を検証する
5. WHEN デプロイメントが失敗した時、THE CDK_Stack SHALL 明確なエラーメッセージを提供し、自動的にロールバックする

### 要件9: ローカル開発環境サポート（LocalStack）

**ユーザーストーリー:** 開発者として、ローカル環境でAWSサービスをエミュレートしたい。そうすることで、AWS料金を気にせずに開発・テストを行い、高速なフィードバックループを実現できる。

#### 受入基準

1. THE CDK_Stack SHALL LocalStack環境での動作をサポートする
2. WHEN 環境パラメータが"local"の時、THE CDK_Stack SHALL LocalStackエンドポイントを使用する
3. THE CDK_Stack SHALL LocalStack用のDocker Compose設定を提供する
4. THE CDK_Stack SHALL ローカル環境と実AWS環境で同一のリソース構成を維持する
5. THE CDK_Stack SHALL LocalStack環境でのテスト実行をサポートする
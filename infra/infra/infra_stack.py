from aws_cdk import (
    Duration,
    Stack,
    Tags,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct
from typing import Optional

class DailyCheckinStack(Stack):
    """
    デイリーチェックインアプリケーション用のCDKスタック
    既存の手動デプロイされたインフラをIaC化
    Lambda関数の拡張を考慮したメソッド分割構成
    """

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        environment: str = "dev",
        project_name: str = "daily-checkin",
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 環境パラメータの設定
        self.env_name = environment
        self.project_name = project_name
        self.is_local = environment == "local"
        
        # 一貫した命名規則の実装
        self.resource_prefix = f"{project_name}-{environment}"
        
        # LocalStack用の設定
        if self.is_local:
            self._configure_localstack()
        
        # すべてのリソースに共通タグを設定
        self._apply_common_tags()
        
        # コンポーネント別にリソースを作成（将来の拡張性を考慮）
        # 1. 共通リソース（データベース）
        self.dynamodb_table = self._create_database()
        
        # 2. Lambda関数群（機能別に整理）
        self.submit_function = self._create_submit_lambda()
        
        # 3. フロントエンドリソース
        self.s3_bucket = self._create_static_website()
        self.cloudfront_distribution = self._create_cdn()
        
        # 4. S3バケットデプロイメント（CloudFrontディストリビューション作成後）
        self._deploy_static_assets()
        
        # 5. 出力値の設定
        self._create_outputs()

    def _apply_common_tags(self) -> None:
        """
        すべてのリソースに環境とプロジェクト識別子でタグ付け
        要件 7.3 に対応
        """
        Tags.of(self).add("Environment", self.env_name)
        Tags.of(self).add("Project", self.project_name)
        Tags.of(self).add("ManagedBy", "CDK")
        Tags.of(self).add("Application", "DailyCheckin")

    def _create_database(self) -> dynamodb.Table:
        """
        DynamoDBテーブルの作成
        将来的に複数のLambda関数から共有される
        
        要件 5.1: 既存の"DailyHealthLog"テーブルと同じスキーマでDynamoDBテーブルを作成
        要件 5.2: パーティションキーとして"Date"を持つ（文字列型）
        要件 5.3: ソートキーとして"Period"を持つ（文字列型）
        要件 5.4: コスト最適化のためにオンデマンド課金モードを使用
        要件 5.5: データ保護のためにポイントインタイムリカバリを有効
        """
        table = dynamodb.Table(
            self, "DailyHealthLogTable",
            table_name="DailyHealthLog",
            partition_key=dynamodb.Attribute(
                name="Date",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="Period", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=self._get_removal_policy()
        )
        
        return table

    def _create_lambda_execution_role(self) -> iam.Role:
        """
        Lambda関数用のカスタムIAMロールを作成
        最小権限の原則に従った権限設定
        
        要件 6.1: 最小限の必要な権限を持つIAMロールを持つ
        要件 6.3: CloudWatchへのログ書き込み権限を持つ
        要件 6.5: 過度に許可的なIAMポリシーを作成してはならない
        """
        # Lambda実行用の基本ロール
        lambda_role = iam.Role(
            self, "SubmitCheckinLambdaRole",
            role_name=f"{self.resource_prefix}-submit-checkin-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="デイリーチェックイン送信Lambda関数用の最小権限ロール"
        )
        
        # CloudWatchログ書き込み権限を付与
        # 要件 6.3: CloudWatchへのログ書き込み権限を持つ
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicExecutionRole"
            )
        )
        
        # VPC内でLambdaを実行する場合のネットワーク権限（現在は不要だが将来の拡張性を考慮）
        # lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name(
        #         "service-role/AWSLambdaVPCAccessExecutionRole"
        #     )
        # )
        
        return lambda_role

    def _create_submit_lambda(self) -> _lambda.Function:
        """
        フォーム送信処理用Lambda関数
        既存のsubmit_daily_checkin.pyを使用
        
        要件 3.1: 既存のlamda/submit_daily_checkin.pyファイルを使用してLambda関数を作成
        要件 3.2: 既存コードと互換性のあるPython 3.9以降のランタイムで設定
        要件 3.4: DynamoDBテーブル名用の環境変数を設定
        要件 3.5: 既存の処理要件に対応するために少なくとも30秒のタイムアウトを持つ
        """
        # Lambda関数用のカスタムIAMロールを作成
        # 要件 6.1: 最小限の必要な権限を持つIAMロールを持つ
        lambda_role = self._create_lambda_execution_role()
        
        lambda_function = _lambda.Function(
            self, "SubmitCheckinFunction",
            function_name=f"{self.resource_prefix}-submit-checkin",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("../lamda"),  # 既存のlamdaディレクトリを使用
            handler="submit_daily_checkin.lambda_handler",
            timeout=Duration.seconds(30),
            memory_size=128,  # 最小構成でコスト最適化
            environment={
                "DYNAMODB_TABLE_NAME": self.dynamodb_table.table_name
            },
            description="デイリーチェックインフォーム送信処理用Lambda関数",
            role=lambda_role  # カスタムロールを使用
        )
        
        # DynamoDBテーブルへの書き込み権限を付与
        # 要件 3.3, 6.2: DynamoDBテーブルへのアイテム書き込み権限のみを持つ
        self.dynamodb_table.grant_write_data(lambda_function)
        
        return lambda_function

    def _create_static_website(self) -> s3.Bucket:
        """
        静的ウェブサイト用S3バケット
        既存のS3/index.htmlをCDKで管理
        
        要件 1.1: 既存のS3バケット設定と同等の静的ウェブサイトホスティング用バケットを作成
        要件 1.2: 既存のS3/index.htmlファイルを新しいバケットにデプロイする機能を提供
        要件 1.3: ウェブサイトホスティングに適切なパブリック読み取り権限を設定（CloudFront経由のみ）
        要件 1.4: デプロイロールバック機能のためにバージョニングを有効
        要件 1.5: セキュリティベストプラクティスに従ってアクセス制御を設定
        """
        bucket = s3.Bucket(
            self, "StaticWebsiteBucket",
            bucket_name=f"{self.resource_prefix}-static-website",
            versioned=True,  # 要件 1.4: バージョニング有効
            public_read_access=False,  # 要件 1.3: CloudFront経由のみアクセス許可
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,  # 要件 1.5: セキュリティベストプラクティス
            removal_policy=self._get_removal_policy(),
            auto_delete_objects=self.is_local or self.env_name == "dev"  # 開発環境では自動削除
        )
        
        return bucket

    def _create_cdn(self) -> cloudfront.Distribution:
        """
        CloudFrontディストリビューション
        S3バケットをオリジンとするCDN配信
        
        要件 2.1: S3バケットを指すCloudFrontディストリビューションを作成
        要件 2.2: デフォルトでHTTPS有効でコンテンツを配信
        要件 2.3: 適切なTTL設定で静的アセットをキャッシュ
        要件 2.4: デフォルトルートオブジェクトを"index.html"として設定
        """
        # Origin Access Identity (OAI) を作成してS3バケットへの安全なアクセスを提供
        oai = cloudfront.OriginAccessIdentity(
            self, "WebsiteOAI",
            comment=f"{self.resource_prefix} static website OAI"
        )
        
        # S3バケットにOAIからの読み取り権限を付与
        self.s3_bucket.grant_read(oai)
        
        # CloudFrontディストリビューションを作成
        distribution = cloudfront.Distribution(
            self, "WebsiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.s3_bucket, 
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,  # 要件 2.2: HTTPS強制
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED  # 要件 2.3: 静的アセット用最適化キャッシュ
            ),
            default_root_object="index.html",  # 要件 2.4: デフォルトルートオブジェクト
            comment=f"{self.resource_prefix} static website distribution",
            price_class=cloudfront.PriceClass.PRICE_CLASS_100  # コスト最適化のため最小価格クラス
        )
        
        return distribution

    def _deploy_static_assets(self) -> None:
        """
        既存のS3/index.htmlファイルをバケットにデプロイする機能
        BucketDeploymentコンストラクトを使用してCloudFrontキャッシュ無効化も実行
        
        要件 1.2: 既存のS3/index.htmlファイルを新しいバケットにデプロイする機能を提供
        """
        # BucketDeploymentを使用して既存のS3/index.htmlをデプロイ
        s3deploy.BucketDeployment(
            self, "StaticWebsiteDeployment",
            sources=[s3deploy.Source.asset("../S3")],  # S3ディレクトリ内のファイルをデプロイ
            destination_bucket=self.s3_bucket,
            distribution=self.cloudfront_distribution,  # CloudFrontキャッシュ無効化
            distribution_paths=["/*"],  # すべてのパスでキャッシュ無効化
            prune=True,  # 不要なファイルを削除
            retain_on_delete=False if (self.is_local or self.env_name == "dev") else True  # 環境に応じた保持設定
        )

    def _create_outputs(self) -> None:
        """
        重要なリソース識別子の出力
        要件 7.5 に対応
        """
        # TODO: 次のタスクで実装
        pass

    def _get_removal_policy(self) -> RemovalPolicy:
        """
        環境に応じた削除ポリシーを返す
        ローカル環境では削除を許可、本番環境では保持
        """
        if self.is_local or self.env_name == "dev":
            return RemovalPolicy.DESTROY
        else:
            return RemovalPolicy.RETAIN

    def _configure_localstack(self) -> None:
        """
        LocalStack環境用の設定
        要件 9.2 に対応
        """
        # LocalStack用のエンドポイント設定は環境変数で制御
        # AWS_ENDPOINT_URL環境変数が設定されている場合、CDKが自動的に使用
        pass

    # 将来の拡張用メソッド例（コメントアウト）
    # def _create_get_logs_lambda(self) -> _lambda.Function:
    #     """ログ取得用Lambda関数"""
    #     pass
    #
    # def _create_cleanup_lambda(self) -> _lambda.Function:
    #     """古いデータ削除用Lambda関数"""
    #     pass
    #
    # def _create_export_lambda(self) -> _lambda.Function:
    #     """データエクスポート用Lambda関数"""
    #     pass

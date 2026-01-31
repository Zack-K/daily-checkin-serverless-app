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
        """
        Initialize the DailyCheckin CDK stack, configure environment-specific behavior, and provision all stack resources.
        
        Creates and stores environment metadata (env_name, project_name, is_local, resource_prefix), applies common tags, optionally configures LocalStack, and constructs the stack resources in order: DynamoDB table, submit Lambda (with Function URL), S3 static website, CloudFront distribution, deploys static assets, and publishes CloudFormation outputs. Side effects: sets attributes such as dynamodb_table, submit_function, s3_bucket, cloudfront_distribution, and function_url on the stack instance.
        
        Parameters:
            scope (Construct): The parent construct.
            construct_id (str): Logical identifier for this stack.
            environment (str): Deployment environment name (e.g., "dev", "prod", "local"); controls removal policy and local behavior.
            project_name (str): Project name prefix used to build resource names.
            **kwargs: Additional keyword arguments forwarded to the base Stack constructor.
        """
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
        Apply standard tags to all resources in the stack.
        
        Adds these tags to every resource:
        - Environment: the stack environment name
        - Project: the project name
        - ManagedBy: "CDK"
        - Application: "DailyCheckin"
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
        Create and configure the Lambda function that handles form submissions for the application.
        
        The function is built from the existing lamda/submit_daily_checkin code, configured to run on Python 3.9 with a 30-second timeout, and receives the DynamoDB table name via the `DYNAMODB_TABLE_NAME` environment variable. This method also grants the function write access to the stack's DynamoDB table and stores the created Lambda Function URL on `self.function_url`.
        
        Returns:
            _lambda.Function: The created Lambda function resource.
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
        
        # Lambda Function URLの作成
        # 要件 4.1: 直接HTTPアクセス用のLambda Function URLを作成
        # 要件 4.2: フロントエンドアプリケーションからのPOSTリクエストを受け入れる
        # 要件 4.3: CloudFrontドメインからのリクエストを許可するCORSを設定
        # 要件 4.4: パブリックアクセス用にNONE認証タイプを使用
        function_url = lambda_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],  # 本番では特定ドメインに制限を推奨
                allowed_methods=[_lambda.HttpMethod.POST],
                allowed_headers=["Content-Type", "X-Requested-With"],
                max_age=Duration.seconds(300)
            )
        )
        
        # Function URLを属性として保存（出力で使用）
        self.function_url = function_url.url
        
        return lambda_function

    def _create_static_website(self) -> s3.Bucket:
        """
        Create an S3 bucket configured to host the application's static website and to be accessed via CloudFront only.
        
        The bucket is created with versioning enabled, public read disabled, ACLs blocked, environment-aware removal policy, and auto-delete-of-objects enabled for local or dev environments.
        
        Returns:
            s3.Bucket: The created S3 bucket resource.
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
        Create a CloudFront distribution that serves the static website from the stack's S3 bucket.
        
        The distribution is configured with an Origin Access Identity to restrict direct S3 access, redirects HTTP requests to HTTPS, uses an optimized cache policy for static assets, and sets "index.html" as the default root object.
        
        Returns:
            cloudfront.Distribution: The created CloudFront distribution.
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
        Deploy static website files from the local ../S3 directory to the stack's S3 bucket and invalidate the CloudFront cache.
        
        Uses a BucketDeployment to upload files from ../S3, invalidate all CloudFront paths (/*), prune files that are no longer present, and set bucket object retention on deletion depending on whether the stack is local or in the dev environment.
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
        Create CloudFormation outputs for the stack's primary resource identifiers.
        
        Adds outputs for:
        - CloudFrontURL: HTTPS URL of the CloudFront distribution.
        - LambdaFunctionURL: Function URL for the submit Lambda.
        - S3BucketName: name of the static website S3 bucket.
        - DynamoDBTableName: name of the DynamoDB table storing daily health logs.
        """
        # CloudFront URL の出力
        CfnOutput(
            self, "CloudFrontURL",
            value=f"https://{self.cloudfront_distribution.distribution_domain_name}",
            description="CloudFront distribution URL for static website",
            export_name=f"{self.resource_prefix}-cloudfront-url"
        )
        
        # Lambda Function URL の出力
        CfnOutput(
            self, "LambdaFunctionURL",
            value=self.function_url,
            description="Lambda Function URL for form submission",
            export_name=f"{self.resource_prefix}-function-url"
        )
        
        # S3バケット名の出力
        CfnOutput(
            self, "S3BucketName",
            value=self.s3_bucket.bucket_name,
            description="S3 bucket name for static website",
            export_name=f"{self.resource_prefix}-s3-bucket"
        )
        
        # DynamoDBテーブル名の出力
        CfnOutput(
            self, "DynamoDBTableName",
            value=self.dynamodb_table.table_name,
            description="DynamoDB table name for daily health logs",
            export_name=f"{self.resource_prefix}-dynamodb-table"
        )

    def _get_removal_policy(self) -> RemovalPolicy:
        """
        Selects the CloudFormation removal policy based on the deployment environment.
        
        Returns:
            RemovalPolicy: `RemovalPolicy.DESTROY` when running locally or when `env_name` is "dev", `RemovalPolicy.RETAIN` otherwise.
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
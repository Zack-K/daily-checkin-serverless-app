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
        
        # 4. 出力値の設定
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

    def _create_submit_lambda(self) -> _lambda.Function:
        """
        フォーム送信処理用Lambda関数
        既存のsubmit_daily_checkin.pyを使用
        
        要件 3.1: 既存のlamda/submit_daily_checkin.pyファイルを使用してLambda関数を作成
        要件 3.2: 既存コードと互換性のあるPython 3.9以降のランタイムで設定
        要件 3.4: DynamoDBテーブル名用の環境変数を設定
        要件 3.5: 既存の処理要件に対応するために少なくとも30秒のタイムアウトを持つ
        """
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
            description="デイリーチェックインフォーム送信処理用Lambda関数"
        )
        
        # DynamoDBテーブルへの書き込み権限を付与
        # 要件 3.3: 既存のDynamoDBテーブル"DailyHealthLog"への書き込みに適切なIAM権限を持つ
        self.dynamodb_table.grant_write_data(lambda_function)
        
        return lambda_function

    def _create_static_website(self) -> s3.Bucket:
        """
        静的ウェブサイト用S3バケット
        """
        # TODO: 次のタスクで実装
        pass

    def _create_cdn(self) -> cloudfront.Distribution:
        """
        CloudFrontディストリビューション
        """
        # TODO: 次のタスクで実装
        pass

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

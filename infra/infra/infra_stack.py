from aws_cdk import (
    Duration,
    Stack,
    Tags,
    CfnOutput,
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
        self.environment = environment
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
        Tags.of(self).add("Environment", self.environment)
        Tags.of(self).add("Project", self.project_name)
        Tags.of(self).add("ManagedBy", "CDK")
        Tags.of(self).add("Application", "DailyCheckin")

    def _create_database(self) -> dynamodb.Table:
        """
        DynamoDBテーブルの作成
        将来的に複数のLambda関数から共有される
        """
        # TODO: 次のタスクで実装
        pass

    def _create_submit_lambda(self) -> _lambda.Function:
        """
        フォーム送信処理用Lambda関数
        既存のsubmit_daily_checkin.pyを使用
        """
        # TODO: 次のタスクで実装
        pass

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

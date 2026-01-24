# LocalStack環境でのテスト手順

このドキュメントでは、LocalStack環境でDynamoDBテーブルの実装をテストし、Web UIで確認する方法を説明します。

## 🚀 LocalStack環境の起動

### 1. LocalStackコンテナの起動

```bash
cd infra
docker compose -f docker-compose.localstack.yml up -d
```

### 2. LocalStackの起動確認

```bash
curl -s http://localhost:4566/_localstack/health | grep -q "available" && echo "✅ LocalStack ready"
```

## 📊 DynamoDBテーブルの作成とテスト

### 1. DynamoDBテーブルの作成

```bash
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

aws dynamodb create-table \
  --table-name DailyHealthLog \
  --attribute-definitions \
    AttributeName=Date,AttributeType=S \
    AttributeName=Period,AttributeType=S \
  --key-schema \
    AttributeName=Date,KeyType=HASH \
    AttributeName=Period,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

### 2. テストデータの追加

#### 朝のデータ
```bash
aws dynamodb put-item \
  --table-name DailyHealthLog \
  --item '{
    "Date":{"S":"2024-01-25"},
    "Period":{"S":"morning"},
    "Condition":{"S":"良好"},
    "IsRoutine":{"S":"できた"},
    "WorkPlace":{"S":"通所"},
    "WorkDetail":{"S":"CDK実装"},
    "Notes":{"S":"LocalStack Web UI確認用テストデータ"},
    "SleepingHours":{"S":"7.5"},
    "EnergyMorning":{"S":"8"},
    "StaminaMorning":{"S":"7"},
    "Timestamp":{"S":"2024-01-25T09:00:00+09:00"}
  }'
```

#### 夕方のデータ
```bash
aws dynamodb put-item \
  --table-name DailyHealthLog \
  --item '{
    "Date":{"S":"2024-01-25"},
    "Period":{"S":"evening"},
    "Condition":{"S":"普通"},
    "IsRoutine":{"S":"できた"},
    "WorkPlace":{"S":"在宅"},
    "WorkDetail":{"S":"テスト実行"},
    "Notes":{"S":"夕方のテストデータ"},
    "SleepingHours":{"S":"7.0"},
    "EnergyEvening":{"S":"6"},
    "StaminaEvening":{"S":"5"},
    "Timestamp":{"S":"2024-01-25T18:00:00+09:00"}
  }'
```

### 3. データの確認

```bash
aws dynamodb scan --table-name DailyHealthLog \
  --query 'Items[*].{Date:Date.S,Period:Period.S,Condition:Condition.S,Notes:Notes.S}' \
  --output table
```

## 🌐 LocalStack Web UIでの確認

### アクセス方法

**LocalStack Web UI**: https://app.localstack.cloud/inst/default/resources

### 確認できる内容

1. **DynamoDB**:
   - テーブル名: `DailyHealthLog`
   - パーティションキー: `Date` (String)
   - ソートキー: `Period` (String)
   - 課金モード: PAY_PER_REQUEST
   - テストデータ: 朝・夕方の2件

2. **CloudFormation**:
   - スタック名: `DailyCheckin-LocalStack`

3. **SSM Parameters**:
   - `/cdk-bootstrap/hnb659fds/version`: 30

### Web UIでの確認手順

1. ブラウザで https://app.localstack.cloud/inst/default/resources を開く
2. 左側のメニューから「DynamoDB」を選択
3. 「DailyHealthLog」テーブルをクリック
4. 「Items」タブでテストデータを確認
5. 「Overview」タブでテーブル設定を確認

## 🔧 CDKスタックのデプロイ（オプション）

### 1. SSMパラメータの作成

```bash
aws ssm put-parameter \
  --name "/cdk-bootstrap/hnb659fds/version" \
  --value "30" \
  --type "String"
```

### 2. CDKテンプレートの合成

```bash
CDK_DISABLE_LEGACY_EXPORT_WARNING=1 cdk synth \
  --app "python3 app.py" \
  --context environment=local > template.json
```

### 3. CloudFormationスタックの作成

```bash
aws cloudformation create-stack \
  --stack-name DailyCheckin-LocalStack \
  --template-body file://template.json
```

## 🛑 LocalStack環境の停止

```bash
docker compose -f docker-compose.localstack.yml down
```

## 📋 検証された要件

- ✅ **要件 5.1**: 既存の"DailyHealthLog"テーブルと同じスキーマで作成
- ✅ **要件 5.2**: パーティションキー"Date"（文字列型）
- ✅ **要件 5.3**: ソートキー"Period"（文字列型）
- ✅ **要件 5.4**: オンデマンド課金モード
- ✅ **要件 5.5**: ポイントインタイムリカバリ有効
- ✅ **要件 9.1-9.5**: LocalStack環境での動作サポート

## 🎯 テスト結果

- DynamoDBテーブルの作成: ✅ 成功
- データの書き込み: ✅ 成功
- データの読み取り: ✅ 成功
- Web UIでの確認: ✅ 成功
- 日本語データの処理: ✅ 成功
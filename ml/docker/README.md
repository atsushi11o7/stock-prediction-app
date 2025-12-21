# Docker Images for Lambda Deployment

AWS Lambda用のコンテナイメージ。

## イメージ構成

| イメージ | 用途 | サイズ | スケジュール |
|---------|------|--------|-------------|
| `daily` | 日次推論（fetch + predict） | ~300MB | 毎営業日 JST 23:00 |
| `monthly` | 月次ファインチューニング | ~1.5GB | 毎月1日 JST 00:00 |

---

## 前提条件

- AWS CLI設定済み
- Docker インストール済み
- ECRリポジトリ作成済み

---

## ECRリポジトリ作成

```bash
# 日次推論用
aws ecr create-repository \
  --repository-name stock-forecast-daily \
  --region ap-northeast-1

# 月次ファインチューニング用
aws ecr create-repository \
  --repository-name stock-forecast-monthly \
  --region ap-northeast-1
```

---

## ビルド & プッシュ

### 環境変数設定

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=ap-northeast-1
export ECR_REGISTRY=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

### ECRログイン

```bash
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}
```

### 日次推論イメージ

```bash
# ml/ ディレクトリで実行
cd /path/to/ml

# ビルド
docker build -t stock-forecast-daily -f docker/daily/Dockerfile .

# タグ付け
docker tag stock-forecast-daily:latest \
  ${ECR_REGISTRY}/stock-forecast-daily:latest

# プッシュ
docker push ${ECR_REGISTRY}/stock-forecast-daily:latest
```

### 月次ファインチューニングイメージ

```bash
# ビルド
docker build -t stock-forecast-monthly -f docker/monthly/Dockerfile .

# タグ付け
docker tag stock-forecast-monthly:latest \
  ${ECR_REGISTRY}/stock-forecast-monthly:latest

# プッシュ
docker push ${ECR_REGISTRY}/stock-forecast-monthly:latest
```

---

## Lambda関数作成

### 日次推論

```bash
aws lambda create-function \
  --function-name stock-forecast-daily \
  --package-type Image \
  --code ImageUri=${ECR_REGISTRY}/stock-forecast-daily:latest \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-stock-forecast-role \
  --memory-size 512 \
  --timeout 600 \
  --region ${AWS_REGION}
```

### 月次ファインチューニング

```bash
aws lambda create-function \
  --function-name stock-forecast-monthly \
  --package-type Image \
  --code ImageUri=${ECR_REGISTRY}/stock-forecast-monthly:latest \
  --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-stock-forecast-role \
  --memory-size 2048 \
  --timeout 900 \
  --ephemeral-storage Size=2048 \
  --region ${AWS_REGION}
```

---

## IAMロール作成

Lambda用のIAMロールを作成します。

### 信頼ポリシー

```bash
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name lambda-stock-forecast-role \
  --assume-role-policy-document file://trust-policy.json
```

### 権限ポリシー

```bash
cat > permissions-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::stock-forecast-prod-apne1",
        "arn:aws:s3:::stock-forecast-prod-apne1/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name lambda-stock-forecast-role \
  --policy-name stock-forecast-permissions \
  --policy-document file://permissions-policy.json
```

---

## EventBridgeスケジュール設定

### 日次推論（毎営業日 JST 23:00 = UTC 14:00）

```bash
# ルール作成
aws events put-rule \
  --name stock-forecast-daily-schedule \
  --schedule-expression "cron(0 14 ? * MON-FRI *)" \
  --region ${AWS_REGION}

# ターゲット設定
aws events put-targets \
  --rule stock-forecast-daily-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:stock-forecast-daily" \
  --region ${AWS_REGION}

# Lambda権限追加
aws lambda add-permission \
  --function-name stock-forecast-daily \
  --statement-id eventbridge-daily \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:${AWS_REGION}:${AWS_ACCOUNT_ID}:rule/stock-forecast-daily-schedule
```

### 月次ファインチューニング（毎月1日 JST 00:00 = UTC 15:00 前日）

```bash
# ルール作成
aws events put-rule \
  --name stock-forecast-monthly-schedule \
  --schedule-expression "cron(0 15 1 * ? *)" \
  --region ${AWS_REGION}

# ターゲット設定
aws events put-targets \
  --rule stock-forecast-monthly-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:stock-forecast-monthly" \
  --region ${AWS_REGION}

# Lambda権限追加
aws lambda add-permission \
  --function-name stock-forecast-monthly \
  --statement-id eventbridge-monthly \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:${AWS_REGION}:${AWS_ACCOUNT_ID}:rule/stock-forecast-monthly-schedule
```

---

## ローカルテスト

```bash
# 日次推論イメージをローカルで実行
docker run -p 9000:8080 \
  -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
  -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
  stock-forecast-daily:latest

# 別ターミナルでテスト
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{}'
```

---

## イメージ更新

```bash
# 再ビルド & プッシュ後
aws lambda update-function-code \
  --function-name stock-forecast-daily \
  --image-uri ${ECR_REGISTRY}/stock-forecast-daily:latest

aws lambda update-function-code \
  --function-name stock-forecast-monthly \
  --image-uri ${ECR_REGISTRY}/stock-forecast-monthly:latest
```

---

## トラブルシューティング

### イメージサイズが大きすぎる

```bash
# マルチステージビルドを検討
# または不要なファイルを.dockerignoreに追加
```

### Lambda実行時にモジュールが見つからない

```bash
# PYTHONPATH設定を確認
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/src:${PYTHONPATH}"
```

### S3アクセスエラー

```bash
# IAMロールの権限を確認
aws iam get-role-policy \
  --role-name lambda-stock-forecast-role \
  --policy-name stock-forecast-permissions
```

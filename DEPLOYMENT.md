# 🚀 Deployment Guide - Kasparro Backend

This guide covers deploying the Kasparro Backend system to cloud providers (AWS, GCP, Azure) with scheduled ETL and monitoring.

## 📋 Table of Contents

1. [AWS Deployment](#aws-deployment)
2. [GCP Deployment](#gcp-deployment)
3. [Azure Deployment](#azure-deployment)
4. [Scheduling ETL](#scheduling-etl)
5. [Monitoring & Logs](#monitoring--logs)
6. [CI/CD Pipeline](#cicd-pipeline)

---

## AWS Deployment

### Prerequisites
- AWS Account with IAM permissions
- AWS CLI configured
- Docker installed locally

### Step 1: Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name kasparro-backend \
  --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t kasparro-backend:latest .
docker tag kasparro-backend:latest \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/kasparro-backend:latest

# Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/kasparro-backend:latest
```

### Step 2: Deploy Database (RDS)

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier kasparro-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username postgres \
  --master-user-password YourSecurePassword123! \
  --allocated-storage 20 \
  --storage-type gp3 \
  --publicly-accessible false \
  --enable-cloudwatch-logs-exports postgresql \
  --region us-east-1
```

### Step 3: Deploy with ECS Fargate

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name kasparro-cluster --region us-east-1

# Register task definition (save as task-definition.json)
cat > task-definition.json << 'EOF'
{
  "family": "kasparro-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/kasparro-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "DEBUG",
          "value": "false"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:kasparro/db-url"
        },
        {
          "name": "API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:kasparro/api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/kasparro-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region us-east-1

# Create ECS service
aws ecs create-service \
  --cluster kasparro-cluster \
  --service-name kasparro-backend \
  --task-definition kasparro-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<ACCOUNT_ID>:targetgroup/kasparro/xxx,containerName=backend,containerPort=8000 \
  --region us-east-1
```

### Step 4: Schedule ETL with EventBridge

```bash
# Create CloudWatch Logs group
aws logs create-log-group \
  --log-group-name /ecs/kasparro-backend \
  --region us-east-1

# Create EventBridge rule (every 6 hours)
aws events put-rule \
  --name kasparro-etl-schedule \
  --schedule-expression "cron(0 */6 * * ? *)" \
  --state ENABLED \
  --region us-east-1

# Create IAM role for EventBridge-ECS
aws iam create-role \
  --role-name kasparro-eventbridge-ecs-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "events.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach ECS execution policy
aws iam attach-role-policy \
  --role-name kasparro-eventbridge-ecs-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceEventsRole

# Set EventBridge target (ECS task)
aws events put-targets \
  --rule kasparro-etl-schedule \
  --targets "Id"="1","Arn"="arn:aws:ecs:us-east-1:<ACCOUNT_ID>:cluster/kasparro-cluster","RoleArn"="arn:aws:iam::<ACCOUNT_ID>:role/kasparro-eventbridge-ecs-role","EcsParameters"='{"LaunchType":"FARGATE","NetworkConfiguration":{"awsvpcConfiguration":{"Subnets":["subnet-xxx"],"SecurityGroups":["sg-xxx"]}},"TaskDefinitionArn":"arn:aws:ecs:us-east-1:<ACCOUNT_ID>:task-definition/kasparro-backend:1","TaskCount":1}' \
  --region us-east-1
```

### AWS Monitoring

```bash
# View logs in CloudWatch
aws logs tail /ecs/kasparro-backend --follow --region us-east-1

# Create CloudWatch alarm for API health
aws cloudwatch put-metric-alarm \
  --alarm-name kasparro-api-health \
  --alarm-description "Alert if API is unhealthy" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region us-east-1
```

---

## GCP Deployment

### Prerequisites
- GCP Project with billing enabled
- Google Cloud SDK installed and authenticated
- Docker installed

### Step 1: Push Docker Image to Artifact Registry

```bash
# Create repository
gcloud artifacts repositories create kasparro \
  --repository-format=docker \
  --location=us-central1

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and tag image
docker build -t kasparro-backend:latest .
docker tag kasparro-backend:latest \
  us-central1-docker.pkg.dev/PROJECT_ID/kasparro/backend:latest

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/PROJECT_ID/kasparro/backend:latest
```

### Step 2: Deploy Database (Cloud SQL)

```bash
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create kasparro-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-auto-increase \
  --backup-start-time=03:00

# Create database
gcloud sql databases create kasparro --instance=kasparro-db

# Create user
gcloud sql users create postgres \
  --instance=kasparro-db \
  --password
```

### Step 3: Deploy with Cloud Run

```bash
# Deploy service
gcloud run deploy kasparro-backend \
  --image us-central1-docker.pkg.dev/PROJECT_ID/kasparro/backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production,DEBUG=false" \
  --set-secrets="DATABASE_URL=kasparro-db-url:latest,API_KEY=kasparro-api-key:latest"
```

### Step 4: Schedule ETL with Cloud Scheduler

```bash
# Create Cloud Scheduler job (every 6 hours)
gcloud scheduler jobs create http kasparro-etl \
  --schedule="0 */6 * * *" \
  --uri="https://YOUR_CLOUD_RUN_URL/run-etl" \
  --http-method=POST \
  --location=us-central1 \
  --oidc-service-account-email=kasparro-etl@PROJECT_ID.iam.gserviceaccount.com
```

### GCP Monitoring

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=kasparro-backend" \
  --limit=50 \
  --format=json

# Create uptime check
gcloud monitoring uptime create https://YOUR_CLOUD_RUN_URL/health \
  --display-name="Kasparro Backend Health"
```

---

## Azure Deployment

### Prerequisites
- Azure Account
- Azure CLI installed and authenticated
- Docker installed

### Step 1: Push Docker Image to ACR

```bash
# Create Azure Container Registry
az acr create \
  --resource-group kasparro-rg \
  --name kasparroregistry \
  --sku Basic

# Build and push image directly to ACR
az acr build \
  --registry kasparroregistry \
  --image kasparro-backend:latest .

# Or push manually
az acr login --name kasparroregistry
docker tag kasparro-backend:latest kasparroregistry.azurecr.io/kasparro-backend:latest
docker push kasparroregistry.azurecr.io/kasparro-backend:latest
```

### Step 2: Deploy Database (Azure Database for PostgreSQL)

```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group kasparro-rg \
  --name kasparro-db \
  --location eastus \
  --admin-user postgres \
  --admin-password YourSecurePassword123! \
  --sku-name B_Gen5_1 \
  --storage-size 51200 \
  --backup-retention 7 \
  --geo-redundant-backup Disabled

# Create database
az postgres db create \
  --resource-group kasparro-rg \
  --server-name kasparro-db \
  --name kasparro
```

### Step 3: Deploy with Container Instances or App Service

```bash
# Using Container Instances (simpler)
az container create \
  --resource-group kasparro-rg \
  --name kasparro-backend \
  --image kasparroregistry.azurecr.io/kasparro-backend:latest \
  --cpu 1 \
  --memory 1 \
  --registry-login-server kasparroregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --environment-variables ENVIRONMENT=production DEBUG=false \
  --secure-environment-variables DATABASE_URL=<connection-string> API_KEY=<api-key> \
  --dns-name-label kasparro-backend \
  --ports 8000
```

### Step 4: Schedule ETL with Azure Logic Apps or Azure Functions

```bash
# Create Azure Function for ETL
func init kasparro-etl-func --python
cd kasparro-etl-func
func new --name etl_trigger --template "Timer trigger"

# Deploy function
func azure functionapp publish kasparro-etl-func

# Create scheduled task (via Azure Portal or CLI)
```

---

## Scheduling ETL

### Manual Trigger
```bash
# Trigger ETL via API (if endpoint exists)
curl -X POST http://YOUR_API_URL/trigger-etl \
  -H "Content-Type: application/json"
```

### Programmatic Trigger
```python
# In your app, add this endpoint
from fastapi import FastAPI
from src.ingestion.runner import run_etl_with_backoff

@app.post("/trigger-etl")
async def trigger_etl():
    result = await run_etl_with_backoff(ETL_SOURCES)
    return {"status": "completed", "result": result}
```

---

## Monitoring & Logs

### CloudWatch / Stackdriver / Application Insights
- Monitor API latency
- Track ETL run metrics
- Alert on failures
- View structured JSON logs

### Example Log Query (CloudWatch Insights)
```sql
fields @timestamp, @message, @level, duration_ms
| filter @message like /ETL/
| stats avg(duration_ms) as avg_duration, max(duration_ms) as max_duration by source
```

---

## CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker image
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster kasparro-cluster \
            --service kasparro-backend \
            --force-new-deployment
```

---

## Verification Checklist

- [ ] Docker image runs locally: `docker run -p 8000:8000 image-name`
- [ ] API health check responds: `curl http://localhost:8000/health`
- [ ] Database connection works
- [ ] ETL runs successfully
- [ ] Cloud deployment URL accessible
- [ ] Scheduled ETL executes on schedule
- [ ] Logs visible in cloud console
- [ ] Metrics are being collected

---

## Troubleshooting

### API Won't Start
```bash
# Check logs
kubectl logs -f deployment/kasparro-backend  # Kubernetes
docker logs container-id                      # Docker
gcloud logging read "resource.type=cloud_run_revision"  # GCP
```

### Database Connection Failed
- Verify connection string in secrets
- Check security groups/firewall rules
- Ensure database is running and accessible

### ETL Not Running
- Check scheduler configuration
- Verify IAM/service account permissions
- Review ETL logs in CloudWatch/Stackdriver

---

## Cost Optimization

- Use spot instances for non-critical workloads
- Set auto-scaling based on metrics
- Implement data retention policies
- Use database reserved instances for long-term deployments

---

For more details, see [README.md](README.md)

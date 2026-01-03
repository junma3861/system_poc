# AWS Deployment Guide

## 🚀 Deploying to AWS

This guide covers deploying the Recommendation System to AWS using ECS Fargate and ECR.

---

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
   ```bash
   brew install awscli
   aws configure
   ```
3. **Docker** installed and running
4. **OpenAI API Key** for chatbot functionality

---

## Quick Deployment (5 Steps)

### Step 1: Set Up AWS Infrastructure

Run the automated infrastructure setup:

```bash
./setup-aws-infrastructure.sh
```

This creates:
- CloudWatch Log Group for ECS logs
- AWS Secrets Manager secret for OpenAI API key
- ECS Cluster
- Security Groups
- IAM Roles

### Step 2: Set Up Managed Databases

You have two options:

#### Option A: Use AWS Managed Services (Recommended)

**RDS PostgreSQL:**
```bash
aws rds create-db-instance \
    --db-instance-identifier recommendation-postgres \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.10 \
    --master-username postgres \
    --master-user-password YourSecurePassword123 \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --publicly-accessible
```

**DocumentDB (MongoDB compatible):**
```bash
aws docdb create-db-cluster \
    --db-cluster-identifier recommendation-docdb \
    --engine docdb \
    --master-username admin \
    --master-user-password YourSecurePassword123 \
    --vpc-security-group-ids sg-xxxxx
```

**ElastiCache Redis:**
```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id recommendation-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --security-group-ids sg-xxxxx
```

#### Option B: Use Docker Compose for Testing

```bash
docker-compose up -d postgres mongodb redis
```

### Step 3: Build and Push Docker Image to ECR

```bash
export AWS_REGION=us-east-1  # Change to your region
./deploy-ecr.sh
```

This script will:
- Create ECR repository if it doesn't exist
- Build Docker image
- Tag and push to ECR

### Step 4: Update Task Definition

Edit `ecs-task-definition.json`:

1. Replace `{AWS_ACCOUNT_ID}` with your AWS account ID
2. Replace `{AWS_REGION}` with your region (e.g., us-east-1)
3. Update database endpoints:
   - `SQL_DATABASE_URL`: Your RDS endpoint
   - `MONGO_URI`: Your DocumentDB endpoint
   - `REDIS_HOST`: Your ElastiCache endpoint

Example:
```json
{
  "name": "SQL_DATABASE_URL",
  "value": "postgresql://postgres:password@recommendation-postgres.xxxxx.us-east-1.rds.amazonaws.com:5432/recommendation_db"
}
```

### Step 5: Deploy ECS Service

```bash
# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition.json \
    --region us-east-1

# Create service
aws ecs create-service \
    --cluster recommendation-system \
    --service-name recommendation-service \
    --task-definition recommendation-system \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
    --region us-east-1
```

---

## Local Docker Testing

Before deploying to AWS, test locally with Docker Compose:

### 1. Set Environment Variables

Create `.env.docker`:
```bash
OPENAI_API_KEY=your_key_here
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Redis (port 6379)
- FastAPI app (port 8000)

### 3. Initialize Database

```bash
# Wait for databases to be ready
sleep 10

# Initialize schema
docker-compose exec app python example.py
```

### 4. Test the Application

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me laptops", "user_id": 1}'
```

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
```

### 6. Stop Services

```bash
docker-compose down

# Remove volumes (data)
docker-compose down -v
```

---

## AWS Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Cloud                             │
│                                                          │
│  ┌──────────────┐     ┌─────────────────────────────┐  │
│  │ Application  │────▶│  ECS Fargate Cluster        │  │
│  │ Load Balancer│     │  ┌─────────────────────┐    │  │
│  │ (ALB)        │     │  │ recommendation-app  │    │  │
│  └──────────────┘     │  │ (Container)         │    │  │
│         │              │  └─────────────────────┘    │  │
│         │              └─────────────────────────────┘  │
│         │                          │                    │
│         │                          │                    │
│  ┌──────▼──────────────────────────▼──────────────┐   │
│  │          Backend Services                       │   │
│  │                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ RDS          │  │ DocumentDB   │           │   │
│  │  │ PostgreSQL   │  │ (MongoDB)    │           │   │
│  │  └──────────────┘  └──────────────┘           │   │
│  │                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ ElastiCache  │  │ Secrets      │           │   │
│  │  │ Redis        │  │ Manager      │           │   │
│  │  └──────────────┘  └──────────────┘           │   │
│  │                                                  │   │
│  │  ┌──────────────┐                               │   │
│  │  │ CloudWatch   │                               │   │
│  │  │ Logs         │                               │   │
│  │  └──────────────┘                               │   │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          ECR (Container Registry)                 │  │
│  │  recommendation-system:latest                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Cost Estimation (Monthly)

### Minimal Setup (Development):
- **ECS Fargate** (1 task, 1 vCPU, 2GB): ~$30
- **RDS db.t3.micro**: ~$15
- **DocumentDB (smallest)**: ~$50
- **ElastiCache t3.micro**: ~$15
- **ALB**: ~$20
- **Data Transfer**: ~$10
- **Total**: ~$140/month

### Production Setup:
- **ECS Fargate** (3 tasks, auto-scaling): ~$100
- **RDS db.t3.small (Multi-AZ)**: ~$60
- **DocumentDB cluster**: ~$150
- **ElastiCache (with replica)**: ~$50
- **ALB**: ~$25
- **Data Transfer**: ~$50
- **Total**: ~$435/month

---

## Environment Variables Reference

Required in ECS task definition or `.env`:

```bash
# Database Connections
SQL_DATABASE_URL=postgresql://user:pass@host:5432/recommendation_db
MONGO_URI=mongodb://host:27017/
MONGO_DATABASE=recommendation_db

# Redis
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_DB=0

# OpenAI (Store in Secrets Manager)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Memory Configuration
SESSION_TTL=3600
MAX_CONTEXT_MESSAGES=10

# Application
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Monitoring & Logging

### CloudWatch Logs

View logs:
```bash
aws logs tail /ecs/recommendation-system --follow
```

### CloudWatch Metrics

Key metrics to monitor:
- CPU utilization
- Memory utilization
- Request count
- Response time
- Error rate

### Set Up Alarms

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name recommendation-high-cpu \
    --alarm-description "Alert when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting

### Container won't start?

1. **Check logs:**
   ```bash
   aws logs tail /ecs/recommendation-system --follow
   ```

2. **Verify environment variables** in task definition

3. **Test database connectivity:**
   ```bash
   # From ECS task
   pg_isready -h rds-endpoint -U postgres
   ```

### High response times?

1. **Scale up tasks:**
   ```bash
   aws ecs update-service \
       --cluster recommendation-system \
       --service recommendation-service \
       --desired-count 3
   ```

2. **Increase container resources** (CPU/memory)

3. **Check database performance** (CloudWatch RDS metrics)

### Out of memory errors?

1. **Increase memory in task definition:**
   ```json
   "memory": "4096"
   ```

2. **Optimize Redis cache settings:**
   ```bash
   SESSION_TTL=1800  # Reduce from 3600
   MAX_CONTEXT_MESSAGES=5  # Reduce from 10
   ```

---

## Security Best Practices

1. **Use AWS Secrets Manager** for sensitive data
2. **Enable VPC endpoints** for private AWS service access
3. **Use IAM roles** instead of access keys
4. **Enable encryption** at rest and in transit
5. **Implement WAF** rules for API protection
6. **Use private subnets** for ECS tasks
7. **Regular security patching** of dependencies

---

## CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        run: |
          aws ecr get-login-password | docker login --username AWS \
            --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com
      
      - name: Build and push
        run: |
          docker build -t recommendation-system .
          docker tag recommendation-system:latest \
            ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com/recommendation-system:latest
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com/recommendation-system:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster recommendation-system \
            --service recommendation-service \
            --force-new-deployment
```

---

## Useful Commands

```bash
# View running tasks
aws ecs list-tasks --cluster recommendation-system

# Describe task
aws ecs describe-tasks --cluster recommendation-system --tasks task-id

# Update service (force new deployment)
aws ecs update-service \
    --cluster recommendation-system \
    --service recommendation-service \
    --force-new-deployment

# Scale service
aws ecs update-service \
    --cluster recommendation-system \
    --service recommendation-service \
    --desired-count 3

# View service events
aws ecs describe-services \
    --cluster recommendation-system \
    --services recommendation-service \
    --query 'services[0].events'
```

---

## Next Steps

1. **Set up Application Load Balancer** for HTTPS
2. **Configure auto-scaling** based on CPU/memory
3. **Implement health checks** and monitoring
4. **Set up backup strategy** for databases
5. **Configure CloudFront** for static assets (UI)
6. **Implement rate limiting** and API throttling
7. **Set up staging environment** for testing

---

## Support Resources

- **AWS ECS Documentation**: https://docs.aws.amazon.com/ecs/
- **AWS ECR Documentation**: https://docs.aws.amazon.com/ecr/
- **Docker Documentation**: https://docs.docker.com/
- **Project Documentation**: See README.md and other docs/

---

**Ready to deploy? Start with `./setup-aws-infrastructure.sh`** 🚀

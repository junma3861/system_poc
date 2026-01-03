#!/bin/bash

# AWS Infrastructure Setup Script
# Creates necessary AWS resources for the Recommendation System

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="recommendation-system"

echo "🏗️  AWS Infrastructure Setup"
echo "=============================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install with: brew install awscli"
    exit 1
fi

echo "✓ AWS CLI found"
echo ""

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo ""

# 1. Create CloudWatch Log Group
echo "📊 Creating CloudWatch Log Group..."
aws logs create-log-group \
    --log-group-name "/ecs/$PROJECT_NAME" \
    --region $AWS_REGION 2>/dev/null || echo "Log group may already exist"

aws logs put-retention-policy \
    --log-group-name "/ecs/$PROJECT_NAME" \
    --retention-in-days 7 \
    --region $AWS_REGION

echo "✓ Log group created"
echo ""

# 2. Create Secrets Manager secret for OpenAI API key
echo "🔐 Creating Secrets Manager secret..."
echo "Enter your OpenAI API key:"
read -s OPENAI_API_KEY

aws secretsmanager create-secret \
    --name "$PROJECT_NAME/openai-api-key" \
    --description "OpenAI API key for recommendation system" \
    --secret-string "$OPENAI_API_KEY" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id "$PROJECT_NAME/openai-api-key" \
    --secret-string "$OPENAI_API_KEY" \
    --region $AWS_REGION

echo "✓ Secret stored"
echo ""

# 3. Create VPC and Subnets (if needed)
echo "🌐 Checking VPC..."
DEFAULT_VPC=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" \
    --output text \
    --region $AWS_REGION)

if [ "$DEFAULT_VPC" != "None" ] && [ ! -z "$DEFAULT_VPC" ]; then
    echo "✓ Using default VPC: $DEFAULT_VPC"
    VPC_ID=$DEFAULT_VPC
    
    # Get subnets
    SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --query "Subnets[].SubnetId" \
        --output text \
        --region $AWS_REGION)
    echo "✓ Found subnets: $SUBNETS"
else
    echo "⚠️  No default VPC found. You may need to create one."
fi
echo ""

# 4. Create Security Group for ECS tasks
echo "🔒 Creating Security Group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name "$PROJECT_NAME-ecs-sg" \
    --description "Security group for recommendation system ECS tasks" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=$PROJECT_NAME-ecs-sg" \
        --query "SecurityGroups[0].GroupId" \
        --output text \
        --region $AWS_REGION)

# Allow inbound on port 8000
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION 2>/dev/null || echo "Ingress rule may already exist"

echo "✓ Security Group created: $SG_ID"
echo ""

# 5. Create ECS Cluster
echo "🚢 Creating ECS Cluster..."
aws ecs create-cluster \
    --cluster-name $PROJECT_NAME \
    --region $AWS_REGION \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 2>/dev/null || \
    echo "Cluster may already exist"

echo "✓ ECS Cluster created"
echo ""

# 6. Create IAM roles
echo "👤 Creating IAM roles..."

# ECS Task Execution Role
cat > /tmp/ecs-task-execution-role-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file:///tmp/ecs-task-execution-role-trust-policy.json 2>/dev/null || \
    echo "Execution role may already exist"

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess 2>/dev/null

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite 2>/dev/null

echo "✓ IAM roles configured"
echo ""

# Summary
echo "✅ Infrastructure Setup Complete!"
echo ""
echo "📋 Resources Created:"
echo "  - CloudWatch Log Group: /ecs/$PROJECT_NAME"
echo "  - Secret: $PROJECT_NAME/openai-api-key"
echo "  - Security Group: $SG_ID"
echo "  - ECS Cluster: $PROJECT_NAME"
echo "  - IAM Roles: ecsTaskExecutionRole"
echo ""
echo "🔧 Configuration for deployment:"
echo "  VPC_ID=$VPC_ID"
echo "  SUBNETS=$SUBNETS"
echo "  SECURITY_GROUP=$SG_ID"
echo ""
echo "🚀 Next steps:"
echo "1. Set up RDS PostgreSQL database"
echo "2. Set up DocumentDB or MongoDB Atlas"
echo "3. Set up ElastiCache Redis"
echo "4. Update ecs-task-definition.json with database endpoints"
echo "5. Run: ./deploy-ecr.sh to push Docker image"
echo "6. Deploy ECS service with task definition"
echo ""

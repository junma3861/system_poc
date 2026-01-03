#!/bin/bash

# AWS ECR Deployment Script for Recommendation System
# This script builds, tags, and pushes the Docker image to AWS ECR

set -e  # Exit on error

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY_NAME="recommendation-system"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "🚀 AWS ECR Deployment Script"
echo "============================"
echo ""
echo "Region: $AWS_REGION"
echo "Repository: $ECR_REPOSITORY_NAME"
echo "Tag: $IMAGE_TAG"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed"
    echo "Install it with: brew install awscli"
    exit 1
fi

echo "✓ AWS CLI found"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "✓ Docker is running"

# Get AWS account ID
echo ""
echo "📋 Getting AWS account information..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ Failed to get AWS account ID"
    echo "Make sure you're authenticated with AWS CLI"
    echo "Run: aws configure"
    exit 1
fi

echo "✓ AWS Account ID: $AWS_ACCOUNT_ID"

# Construct ECR repository URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

# Check if ECR repository exists, create if not
echo ""
echo "🔍 Checking ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION &> /dev/null; then
    echo "✓ ECR repository exists"
else
    echo "📦 Creating ECR repository..."
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    echo "✓ ECR repository created"
fi

# Authenticate Docker to ECR
echo ""
echo "🔐 Authenticating Docker to ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_URI

echo "✓ Docker authenticated to ECR"

# Build Docker image
echo ""
echo "🔨 Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .

echo "✓ Docker image built"

# Tag image for ECR
echo ""
echo "🏷️  Tagging image for ECR..."
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$(date +%Y%m%d-%H%M%S)

echo "✓ Image tagged"

# Push to ECR
echo ""
echo "⬆️  Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG
docker push $ECR_URI:$(date +%Y%m%d-%H%M%S)

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📦 Image URI: $ECR_URI:$IMAGE_TAG"
echo ""
echo "🚀 Next steps:"
echo "1. Use this image in ECS, EKS, or EC2"
echo "2. Configure environment variables (OPENAI_API_KEY, database connections)"
echo "3. Set up RDS for PostgreSQL, DocumentDB for MongoDB"
echo "4. Configure ElastiCache for Redis"
echo ""
echo "Example ECS task definition:"
echo "  Image: $ECR_URI:$IMAGE_TAG"
echo "  Port: 8000"
echo "  Environment variables: See .env.example"
echo ""

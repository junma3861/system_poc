#!/bin/bash

# =============================================================================
# Complete Setup Script for AI Recommendation System
# =============================================================================
# This script sets up all required dependencies:
# - PostgreSQL (product catalog)
# - MongoDB (conversation history) - optional
# - Redis (session memory) - optional
# =============================================================================

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AI Recommendation System - Complete Setup                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS_TYPE=$(uname -s)
echo "🖥️  Detected OS: $OS_TYPE"
echo ""

# =============================================================================
# PostgreSQL Setup (REQUIRED)
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊  PostgreSQL Setup (Required)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL is installed"
    
    if pg_isready &> /dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL is running"
    else
        echo -e "${YELLOW}⚠${NC}  PostgreSQL not running"
        read -p "Start PostgreSQL now? (y/n): " start_pg
        if [[ "$start_pg" == "y" ]]; then
            if [[ "$OS_TYPE" == "Darwin" ]]; then
                brew services start postgresql@14 || brew services start postgresql
            else
                sudo systemctl start postgresql
            fi
            echo -e "${GREEN}✓${NC} PostgreSQL started"
        fi
    fi
else
    echo -e "${RED}✗${NC} PostgreSQL not installed"
    read -p "Install PostgreSQL now? (y/n): " install_pg
    
    if [[ "$install_pg" == "y" ]]; then
        if [[ "$OS_TYPE" == "Darwin" ]]; then
            echo "Installing via Homebrew..."
            brew install postgresql@14
            brew services start postgresql@14
        else
            echo "Installing via apt..."
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        fi
        echo -e "${GREEN}✓${NC} PostgreSQL installed and started"
    else
        echo -e "${RED}✗${NC} PostgreSQL required. Exiting."
        exit 1
    fi
fi

# Create database
if pg_isready &> /dev/null; then
    echo ""
    echo "Creating database..."
    createdb recommendation_db 2>/dev/null && echo -e "${GREEN}✓${NC} Database 'recommendation_db' created" || echo -e "${BLUE}ℹ${NC}  Database already exists"
fi

echo ""

# =============================================================================
# MongoDB Setup (OPTIONAL but recommended)
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🍃  MongoDB Setup (Optional - for conversation history)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Install MongoDB? (recommended, y/n): " install_mongo_choice

if [[ "$install_mongo_choice" == "y" ]]; then
    if command -v mongod &> /dev/null; then
        echo -e "${GREEN}✓${NC} MongoDB is installed"
        
        if pgrep -x mongod &> /dev/null; then
            echo -e "${GREEN}✓${NC} MongoDB is running"
        else
            echo "Starting MongoDB..."
            if [[ "$OS_TYPE" == "Darwin" ]]; then
                brew services start mongodb-community
            else
                sudo systemctl start mongod
                sudo systemctl enable mongod
            fi
            echo -e "${GREEN}✓${NC} MongoDB started"
        fi
    else
        if [[ "$OS_TYPE" == "Darwin" ]]; then
            echo "Installing via Homebrew..."
            brew tap mongodb/brew
            brew install mongodb-community
            brew services start mongodb-community
            echo -e "${GREEN}✓${NC} MongoDB installed and started"
        else
            echo -e "${YELLOW}⚠${NC}  For Linux, install MongoDB manually:"
            echo "    https://docs.mongodb.com/manual/installation/"
        fi
    fi
else
    echo -e "${BLUE}ℹ${NC}  Skipping MongoDB (conversation history will be limited)"
fi

echo ""

# =============================================================================
# Redis Setup (OPTIONAL but recommended)
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴  Redis Setup (Optional - for session memory)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Install Redis? (recommended, y/n): " install_redis_choice

if [[ "$install_redis_choice" == "y" ]]; then
    if command -v redis-server &> /dev/null; then
        echo -e "${GREEN}✓${NC} Redis is installed"
    else
        if [[ "$OS_TYPE" == "Darwin" ]]; then
            echo "Installing via Homebrew..."
            brew install redis
        else
            echo "Installing via apt..."
            sudo apt-get install -y redis-server
        fi
        echo -e "${GREEN}✓${NC} Redis installed"
    fi
    
    echo "Starting Redis..."
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        brew services start redis
    else
        sudo systemctl start redis
        sudo systemctl enable redis
    fi
    
    sleep 2
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓${NC} Redis is running"
    else
        echo -e "${YELLOW}⚠${NC}  Redis may not be running properly"
    fi
else
    echo -e "${BLUE}ℹ${NC}  Skipping Redis (session memory will use fallback)"
fi

echo ""

# =============================================================================
# Python Environment Setup
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍  Python Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "requirements.txt" ]; then
    echo "Installing Python packages..."
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${YELLOW}⚠${NC}  requirements.txt not found"
fi

echo ""

# =============================================================================
# Configuration
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️   Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env from .env.example"
    else
        echo -e "${YELLOW}⚠${NC}  .env.example not found"
    fi
fi

# Get current username for PostgreSQL
CURRENT_USER=$(whoami)

# Update .env with correct PostgreSQL URL
if [ -f ".env" ]; then
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        # macOS uses system username by default
        sed -i '' "s|SQL_DATABASE_URL=.*|SQL_DATABASE_URL=postgresql://${CURRENT_USER}@localhost:5432/recommendation_db|g" .env
        echo -e "${GREEN}✓${NC} Updated PostgreSQL connection in .env"
    fi
    
    # Check if OpenAI key is set
    if grep -q "your_openai_api_key_here" .env; then
        echo ""
        echo -e "${YELLOW}⚠${NC}  OpenAI API key not set in .env"
        echo "   Get your key from: https://platform.openai.com/api-keys"
        echo "   Then edit .env and add: OPENAI_API_KEY=sk-your-key-here"
    fi
fi

echo ""

# =============================================================================
# Initialize Database
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️   Initialize Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "example.py" ]; then
    read -p "Load sample data now? (y/n): " load_data
    if [[ "$load_data" == "y" ]]; then
        echo "Loading sample data..."
        python example.py
        echo -e "${GREEN}✓${NC} Sample data loaded"
    else
        echo -e "${BLUE}ℹ${NC}  Run 'python example.py' later to load sample data"
    fi
else
    echo -e "${YELLOW}⚠${NC}  example.py not found"
fi

echo ""

# =============================================================================
# Summary
# =============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✨ Setup Complete! ✨                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📋 What's Installed:"
echo ""

# Check status of each component
if pg_isready &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL (running)"
else
    echo -e "  ${YELLOW}⚠${NC} PostgreSQL (installed but not running)"
fi

if command -v mongod &> /dev/null && pgrep -x mongod &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} MongoDB (running)"
elif command -v mongod &> /dev/null; then
    echo -e "  ${YELLOW}⚠${NC} MongoDB (installed but not running)"
else
    echo -e "  ${BLUE}○${NC} MongoDB (not installed)"
fi

if command -v redis-server &> /dev/null && redis-cli ping &> /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Redis (running)"
elif command -v redis-server &> /dev/null; then
    echo -e "  ${YELLOW}⚠${NC} Redis (installed but not running)"
else
    echo -e "  ${BLUE}○${NC} Redis (not installed)"
fi

echo ""
echo "🚀 Next Steps:"
echo ""
echo "  1. Add your OpenAI API key to .env file"
echo "     OPENAI_API_KEY=sk-your-key-here"
echo ""
echo "  2. Start the server:"
echo "     uvicorn main:app --reload"
echo ""
echo "  3. Open the web interface:"
echo "     open http://localhost:8000/index.html"
echo ""
echo "  4. Or use Docker (recommended):"
echo "     docker-compose up -d"
echo ""

echo "📖 Documentation:"
echo "  • GETTING_STARTED.md  - Complete setup guide"
echo "  • README.md           - Features & API reference"
echo "  • DOCKER_GUIDE.md     - Docker usage"
echo "  • AWS_DEPLOYMENT.md   - Cloud deployment"
echo ""

echo "🧪 Test the system:"
echo "  python test_chatbot.py"
echo "  python test_memory.py"
echo "  curl http://localhost:8000/health"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "Happy building! 🎉"
echo "═══════════════════════════════════════════════════════════════"

#!/bin/bash

# Prerequisites Check Script for ScriptToDoc Deployment
# This script verifies all required tools and access before deployment

set -e

echo "🔍 Checking Prerequisites for ScriptToDoc Deployment"
echo "=================================================="
echo ""

ERRORS=0

# Check Azure CLI
echo "📋 Checking Azure CLI..."
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install: https://aka.ms/InstallAzureCLI"
    ERRORS=$((ERRORS + 1))
else
    AZ_VERSION=$(az --version | head -n 1)
    echo "✅ Azure CLI installed: $AZ_VERSION"
    
    # Check if logged in
    if ! az account show &> /dev/null; then
        echo "❌ Not logged in to Azure. Please run: az login"
        ERRORS=$((ERRORS + 1))
    else
        SUBSCRIPTION=$(az account show --query name -o tsv)
        SUBSCRIPTION_ID=$(az account show --query id -o tsv)
        echo "✅ Logged in to Azure"
        echo "   Subscription: $SUBSCRIPTION"
        echo "   ID: $SUBSCRIPTION_ID"
    fi
fi
echo ""

# Check Docker
echo "📋 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    ERRORS=$((ERRORS + 1))
else
    DOCKER_VERSION=$(docker --version)
    echo "✅ Docker installed: $DOCKER_VERSION"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running. Please start Docker Desktop"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Docker daemon is running"
        
        # Check for buildx (required for multi-platform builds)
        if docker buildx version &> /dev/null; then
            BUILDX_VERSION=$(docker buildx version | head -n 1)
            echo "✅ Docker buildx available: $BUILDX_VERSION"
        else
            echo "⚠️  Docker buildx not found. Creating buildx builder..."
            docker buildx create --name multiplatform --use 2>/dev/null || true
            echo "✅ Docker buildx builder created"
        fi
    fi
fi
echo ""

# Check Node.js
echo "📋 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+: https://nodejs.org/"
    ERRORS=$((ERRORS + 1))
else
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -lt 18 ]; then
        echo "❌ Node.js version $NODE_VERSION is too old. Please upgrade to Node.js 18+"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Node.js installed: $NODE_VERSION"
    fi
fi
echo ""

# Check Python (for backend)
echo "📋 Checking Python..."
PYTHON_FOUND=false
PYTHON_CMD=""

# Check for python3.11, python3.12, python3.13, etc. first
for PYTHON_VER in python3.13 python3.12 python3.11 python3; do
    if command -v $PYTHON_VER &> /dev/null; then
        PYTHON_VERSION=$($PYTHON_VER --version 2>&1)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d' ' -f2 | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d' ' -f2 | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            echo "✅ Python installed: $PYTHON_VERSION ($PYTHON_VER)"
            PYTHON_FOUND=true
            PYTHON_CMD=$PYTHON_VER
            break
        fi
    fi
done

if [ "$PYTHON_FOUND" = false ]; then
    # Check if any python3 exists
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        PYTHON_MAJOR=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1)
        PYTHON_MINOR=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
            echo "⚠️  Python version $PYTHON_VERSION is installed but Python 3.11+ is recommended"
            echo "   Current version may work for deployment scripts, but backend requires 3.11+"
            echo "   To install Python 3.11+:"
            echo "     macOS: brew install python@3.11"
            echo "     Or download from: https://www.python.org/downloads/"
            echo ""
            echo "   Note: Docker builds will use Python 3.11 from the Dockerfile,"
            echo "   so deployment may still work. Proceeding with warning..."
            # Don't count as error - Docker will handle Python version
        else
            echo "✅ Python installed: $PYTHON_VERSION"
            PYTHON_FOUND=true
        fi
    else
        echo "⚠️  Python 3 not found in PATH"
        echo "   Docker builds will use Python 3.11 from the Dockerfile,"
        echo "   so deployment may still work. Proceeding with warning..."
        # Don't count as error - Docker will handle Python version
    fi
fi
echo ""

# Check Azure CLI extensions
echo "📋 Checking Azure CLI extensions..."
REQUIRED_EXTENSIONS=("containerapp" "application-insights")
for EXT in "${REQUIRED_EXTENSIONS[@]}"; do
    if az extension show --name $EXT &> /dev/null; then
        echo "✅ Extension '$EXT' installed"
    else
        echo "⚠️  Extension '$EXT' not found. Installing..."
        az extension add --name $EXT --yes
        echo "✅ Extension '$EXT' installed"
    fi
done
echo ""

# Check Azure subscription permissions
echo "📋 Checking Azure subscription permissions..."
if az account show &> /dev/null; then
    USER_PRINCIPAL=$(az ad signed-in-user show --query userPrincipalName -o tsv 2>/dev/null || echo "unknown")
    echo "✅ Current user: $USER_PRINCIPAL"
    
    # Try to list resource groups (requires Contributor or Owner role)
    if az group list --query "[].name" -o tsv &> /dev/null; then
        echo "✅ Has permissions to list resource groups (Contributor/Owner role)"
    else
        echo "⚠️  May not have sufficient permissions. Ensure you have Contributor or Owner role"
    fi
fi
echo ""

# Summary
echo "=================================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All prerequisites met! Ready to deploy."
    echo ""
    echo "📝 Next steps:"
    echo "  1. Run: ./check-deployment-state.sh (to check current state)"
    echo "  2. Run: ./deploy-infrastructure.sh (to create Azure resources)"
    exit 0
else
    echo "❌ Found $ERRORS error(s). Please fix the issues above before proceeding."
    exit 1
fi

#!/bin/bash

# Frontend Deployment Script for Vercel

set -e  # Exit on error

echo "🚀 Deploying Frontend to Vercel"
echo "================================"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Vercel CLI not found. Installing..."
    npm install -g vercel
    echo "✅ Vercel CLI installed"
    echo ""
fi

# Navigate to frontend directory
cd ../frontend

echo "📋 Step 1: Building frontend..."
npm install
echo "✅ Dependencies installed"
echo ""

echo "📋 Step 2: Deploying to Vercel (production)..."
echo ""
echo "⚠️  IMPORTANT: When prompted, configure the following:"
echo "  • Framework Preset: Next.js"
echo "  • Build Command: npm run build"
echo "  • Output Directory: .next"
echo "  • Install Command: npm install"
echo ""
echo "After deployment, you'll need to set environment variable:"
echo "  NEXT_PUBLIC_API_URL=https://ca-scripttodoc-prod-api.delightfuldune-05b8c4e7.eastus.azurecontainerapps.io"
echo ""
read -p "Press Enter to continue with Vercel deployment..."

vercel --prod

echo ""
echo "======================================"
echo "✅ Frontend Deployment Complete!"
echo "======================================"
echo ""
echo "📝 Next Steps:"
echo "  1. Set environment variable in Vercel dashboard:"
echo "     https://vercel.com/dashboard"
echo "     NEXT_PUBLIC_API_URL=https://ca-scripttodoc-prod-api.delightfuldune-05b8c4e7.eastus.azurecontainerapps.io"
echo ""
echo "  2. Get your Vercel URL and update API CORS:"
echo "     Edit deployment/backend-api-direct.bicep"
echo "     Replace allowedOrigins: ['*'] with your Vercel URL"
echo "     Then run: cd deployment && ./deploy-backend-with-secrets.sh"
echo ""
echo "  3. Test your application!"
echo ""

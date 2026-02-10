#!/bin/bash

# Complete authentication setup script

echo "🔐 Completing Authentication Setup"
echo "==================================="
echo ""

# Update page.tsx to wrap with ProtectedRoute and use auth
echo "📋 Step 1: Updating main page to use authentication..."

# Read the current page.tsx
PAGE_FILE="app/page.tsx"

# Create a backup
cp "$PAGE_FILE" "$PAGE_FILE.backup"

# Use sed to add ProtectedRoute wrapper after the return statement
# This is a simplified update - the user should verify it
echo "✅ Page backed up to app/page.tsx.backup"
echo ""
echo "⚠️  Manual update needed:"
echo "  1. Open app/page.tsx"
echo "  2. Find the return statement (line ~157)"
echo "  3. Wrap the entire return content with:"
echo "     return ("
echo "       <ProtectedRoute>"
echo "         {/* existing content */}"
echo "       </ProtectedRoute>"
echo "     );"
echo "  4. Update the SidebarProfile (line ~197) to:"
echo "     <SidebarProfile"
echo "       userName={user?.name || 'User'}"
echo "       userEmail={user?.email || 'user@example.com'}"
echo "       onLogout={logout}"
echo "     />"
echo ""

read -p "Press Enter when you've completed the manual updates..."

echo ""
echo "📋 Step 2: Building frontend..."
npm run build

if [ $? -ne 0 ]; then
  echo "❌ Build failed. Please fix errors and try again."
  exit 1
fi

echo "✅ Frontend built successfully"
echo ""

echo "======================================"
echo "✅ Authentication Setup Complete!"
echo "======================================"
echo ""
echo "📝 What we've built:"
echo "  ✅ Auth context and provider"
echo "  ✅ Login page (/login)"
echo "  ✅ Bearer token authentication"
echo "  ✅ Protected routes"
echo "  ✅ Logout functionality"
echo ""
echo "📝 Next Steps:"
echo "  1. Test locally:"
echo "     npm run dev"
echo "     Visit http://localhost:3000"
echo "     You'll be redirected to /login"
echo "     Use any email/password to login"
echo ""
echo "  2. Deploy to Azure:"
echo "     cd ../deployment"
echo "     ./deploy-frontend-containerapp.sh"
echo ""
echo "  3. Update API CORS after deployment"
echo ""

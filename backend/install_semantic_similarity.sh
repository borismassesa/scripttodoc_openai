#!/bin/bash
# Quick fix script to install sentence-transformers

echo "🔧 Installing sentence-transformers for semantic similarity..."
echo ""

# Activate venv
source venv/bin/activate

# Install sentence-transformers
echo "Installing sentence-transformers==2.3.1..."
pip install sentence-transformers==2.3.1

# Verify installation
echo ""
echo "✅ Verifying installation..."
python3 -c "from sentence_transformers import SentenceTransformer; print('✅ sentence-transformers installed successfully!')" && \
echo "✅ Model: all-MiniLM-L6-v2 ready" || \
echo "❌ Installation failed - check errors above"

echo ""
echo "📝 Next steps:"
echo "1. Restart your server: python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo "2. Check logs for: 'INFO: Semantic similarity scoring enabled'"
echo "3. Process a transcript - confidence should be ~0.43 instead of 0.00"
echo ""

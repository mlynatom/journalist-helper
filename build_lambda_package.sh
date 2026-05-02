#!/bin/bash
set -e

# Build script to create a Lambda deployment package using uv

PACKAGE_DIR="lambda_package"
ZIP_FILE="lambda_deployment.zip"

echo "Creating Lambda deployment package..."

# Clean previous builds
rm -rf "$PACKAGE_DIR" "$ZIP_FILE"

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Export dependencies and install into package directory
echo "Installing Python dependencies with uv..."
uv pip install \
  --target "$PACKAGE_DIR" \
  --python 3.14 \
  feedparser \
  openrouter \
  pydantic \
  pydantic-settings \
  python-dotenv \
  redis \
  requests

# Copy source files
echo "Copying source files..."
cp main.py "$PACKAGE_DIR/"
cp lambda_function.py "$PACKAGE_DIR/"
cp -r src "$PACKAGE_DIR/"

# Create zip file
echo "Creating zip archive..."
cd "$PACKAGE_DIR"
zip -r ../"$ZIP_FILE" . -q
cd ..

echo ""
echo "✓ Lambda package created: $ZIP_FILE"
echo ""
echo "Next steps:"
echo "1. Upload $ZIP_FILE to AWS Lambda"
echo "2. Set Handler to: lambda_handler.lambda_handler"
echo "3. Set Runtime to: python3.12"
echo "4. Set Timeout to: 120 seconds"
echo "5. Set Memory to: 1024 MB"
echo "6. Add environment variables:"
echo "   - OPENROUTER_API_KEY"
echo "   - BOT_TOKEN"
echo "   - USER_ID"
echo "   - REDIS_URL"
echo "7. Add EventBridge Schedule rule for cron(0 * * * ? *)"
echo ""
echo "File size: $(du -h $ZIP_FILE | cut -f1)"

#!/bin/bash

###########################################
# XTTS + RVC Voice API Test Script
# Tests all API endpoints
###########################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# API Base URL
API_URL="http://localhost:8001"

echo "=========================================="
echo "Testing XTTS + RVC Voice API"
echo "=========================================="
echo ""

# Check if server is running
echo -e "${BLUE}Checking if server is running...${NC}"
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: API server is not running at $API_URL${NC}"
    echo "Please start the server with ./start.sh"
    exit 1
fi
echo -e "${GREEN}✓ Server is running${NC}"
echo ""

###########################################
# Test 1: Root endpoint
###########################################
echo -e "${BLUE}Test 1: Root endpoint${NC}"
echo "GET $API_URL/"
curl -s "$API_URL/" | jq '.' || curl -s "$API_URL/"
echo ""
echo ""

###########################################
# Test 2: Health check
###########################################
echo -e "${BLUE}Test 2: Health check${NC}"
echo "GET $API_URL/health"
curl -s "$API_URL/health" | jq '.' || curl -s "$API_URL/health"
echo ""
echo ""

###########################################
# Test 3: List RVC models
###########################################
echo -e "${BLUE}Test 3: List RVC models${NC}"
echo "GET $API_URL/list-rvc-models"
MODELS_RESPONSE=$(curl -s "$API_URL/list-rvc-models")
echo "$MODELS_RESPONSE" | jq '.' || echo "$MODELS_RESPONSE"

# Extract first model name for later tests
FIRST_MODEL=$(echo "$MODELS_RESPONSE" | jq -r '.models[0].name // empty' 2>/dev/null)
echo ""
echo ""

###########################################
# Test 4: Supported languages
###########################################
echo -e "${BLUE}Test 4: Supported languages${NC}"
echo "GET $API_URL/supported-languages"
curl -s "$API_URL/supported-languages" | jq '.' || curl -s "$API_URL/supported-languages"
echo ""
echo ""

###########################################
# Test 5: Generate speech (XTTS only)
###########################################
echo -e "${BLUE}Test 5: Generate speech (XTTS only)${NC}"
echo "POST $API_URL/generate-speech"
echo "Request: Simple TTS without RVC"

RESPONSE=$(curl -s -X POST "$API_URL/generate-speech" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the XTTS voice generation system.",
    "language": "en",
    "speed": 1.0,
    "normalize": true
  }')

echo "$RESPONSE" | jq '.' || echo "$RESPONSE"

# Extract audio_id for download test
AUDIO_ID=$(echo "$RESPONSE" | jq -r '.audio_id // empty' 2>/dev/null)

if [ -n "$AUDIO_ID" ]; then
    echo -e "${GREEN}✓ Audio ID: $AUDIO_ID${NC}"
fi
echo ""
echo ""

###########################################
# Test 6: Generate speech with RVC
###########################################
if [ -n "$FIRST_MODEL" ]; then
    echo -e "${BLUE}Test 6: Generate speech with RVC conversion${NC}"
    echo "POST $API_URL/generate-speech"
    echo "Request: TTS + RVC conversion using model: $FIRST_MODEL"
    
    RVC_RESPONSE=$(curl -s -X POST "$API_URL/generate-speech" \
      -H "Content-Type: application/json" \
      -d "{
        \"text\": \"This is a test with voice conversion using $FIRST_MODEL.\",
        \"language\": \"en\",
        \"speed\": 1.0,
        \"rvc_model\": \"$FIRST_MODEL\",
        \"pitch_shift\": 0,
        \"normalize\": true
      }")
    
    echo "$RVC_RESPONSE" | jq '.' || echo "$RVC_RESPONSE"
    
    RVC_AUDIO_ID=$(echo "$RVC_RESPONSE" | jq -r '.audio_id // empty' 2>/dev/null)
    
    if [ -n "$RVC_AUDIO_ID" ]; then
        echo -e "${GREEN}✓ Audio ID: $RVC_AUDIO_ID${NC}"
    fi
    echo ""
    echo ""
else
    echo -e "${YELLOW}⚠ Test 6 skipped: No RVC models found${NC}"
    echo ""
    echo ""
fi

###########################################
# Test 7: Download audio
###########################################
if [ -n "$AUDIO_ID" ]; then
    echo -e "${BLUE}Test 7: Download generated audio${NC}"
    echo "GET $API_URL/download/$AUDIO_ID"
    
    OUTPUT_FILE="test_output.wav"
    
    HTTP_CODE=$(curl -s -o "$OUTPUT_FILE" -w "%{http_code}" "$API_URL/download/$AUDIO_ID")
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
        echo -e "${GREEN}✓ Download successful${NC}"
        echo "  File: $OUTPUT_FILE"
        echo "  Size: $FILE_SIZE bytes"
        
        # Clean up
        rm -f "$OUTPUT_FILE"
    else
        echo -e "${RED}✗ Download failed (HTTP $HTTP_CODE)${NC}"
    fi
    echo ""
    echo ""
else
    echo -e "${YELLOW}⚠ Test 7 skipped: No audio ID from previous test${NC}"
    echo ""
    echo ""
fi

###########################################
# Test 8: Batch generate
###########################################
echo -e "${BLUE}Test 8: Batch generation${NC}"
echo "POST $API_URL/batch-generate"
echo "Request: Generate 3 audio files"

BATCH_RESPONSE=$(curl -s -X POST "$API_URL/batch-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "First test sentence.",
      "Second test sentence.",
      "Third test sentence."
    ],
    "language": "en",
    "speed": 1.0
  }')

echo "$BATCH_RESPONSE" | jq '.' || echo "$BATCH_RESPONSE"
echo ""
echo ""

###########################################
# Test 9: Error handling (invalid request)
###########################################
echo -e "${BLUE}Test 9: Error handling${NC}"
echo "POST $API_URL/generate-speech (invalid - empty text)"

ERROR_RESPONSE=$(curl -s -X POST "$API_URL/generate-speech" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "",
    "language": "en"
  }')

echo "$ERROR_RESPONSE" | jq '.' || echo "$ERROR_RESPONSE"
echo ""
echo ""

###########################################
# Test 10: Download non-existent file
###########################################
echo -e "${BLUE}Test 10: Download non-existent file${NC}"
echo "GET $API_URL/download/nonexistent-id"

NOT_FOUND_RESPONSE=$(curl -s "$API_URL/download/nonexistent-id")
echo "$NOT_FOUND_RESPONSE" | jq '.' || echo "$NOT_FOUND_RESPONSE"
echo ""
echo ""

###########################################
# Summary
###########################################
echo "=========================================="
echo -e "${GREEN}API Testing Complete!${NC}"
echo "=========================================="
echo ""
echo "All endpoint tests have been executed."
echo ""
echo "To test manually, visit:"
echo "  - API Docs: $API_URL/docs"
echo "  - ReDoc: $API_URL/redoc"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Tip: Install 'jq' for better JSON formatting${NC}"
    echo "  sudo apt install jq"
    echo ""
fi


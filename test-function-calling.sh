#!/bin/bash

# Test script for function calling / tool use

echo "=========================================="
echo "Function Calling Test"
echo "=========================================="
echo ""

# Check if Ollama is running
echo "1. Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "✅ Ollama is running"
else
  echo "❌ Ollama is not running!"
  echo "   Start it with: ollama serve"
  exit 1
fi
echo ""

# Check if qwen2.5 is available
echo "2. Checking model availability..."
if ollama list | grep -q "qwen2.5:7b-instruct"; then
  echo "✅ qwen2.5:7b-instruct is available"
else
  echo "⚠️  qwen2.5:7b-instruct not found"
  echo "   Download with: ollama pull qwen2.5:7b-instruct"
  echo ""
  echo "   Checking for llama3.2 as fallback..."
  if ollama list | grep -q "llama3.2"; then
    echo "   ✅ llama3.2 available (fallback)"
    MODEL="llama3.2"
  else
    echo "   ❌ No compatible model found"
    exit 1
  fi
fi
echo ""

# Get model from .env or use default
MODEL=$(grep "OLLAMA_MODEL=" ~/agent/.env 2>/dev/null | cut -d= -f2 || echo "qwen2.5:7b-instruct")
echo "Using model: $MODEL"
echo ""

# Test 1: Weather tool
echo "3. Test 1: Weather Tool"
echo "   Query: 'What's the weather in San Francisco?'"
echo ""

RESPONSE=$(curl -s http://localhost:11434/api/chat -d "{
  \"model\": \"$MODEL\",
  \"messages\": [
    {\"role\": \"user\", \"content\": \"What's the weather in San Francisco?\"}
  ],
  \"tools\": [
    {
      \"type\": \"function\",
      \"function\": {
        \"name\": \"get_weather\",
        \"description\": \"Get the current weather for a location\",
        \"parameters\": {
          \"type\": \"object\",
          \"properties\": {
            \"location\": {
              \"type\": \"string\",
              \"description\": \"The city and state, e.g. San Francisco, CA\"
            }
          },
          \"required\": [\"location\"]
        }
      }
    }
  ],
  \"stream\": false
}")

if echo "$RESPONSE" | grep -q "tool_calls"; then
  echo "   ✅ Model generated tool call"
  TOOL_NAME=$(echo "$RESPONSE" | jq -r '.message.tool_calls[0].function.name' 2>/dev/null)
  TOOL_ARGS=$(echo "$RESPONSE" | jq -r '.message.tool_calls[0].function.arguments' 2>/dev/null)
  echo "   Tool: $TOOL_NAME"
  echo "   Args: $TOOL_ARGS"
else
  echo "   ⚠️  No tool call generated"
  echo "   Response: $(echo "$RESPONSE" | jq -r '.message.content' 2>/dev/null | head -c 100)"
fi
echo ""

# Test 2: Web search tool
echo "4. Test 2: Web Search Tool"
echo "   Query: 'Search for recent AI news'"
echo ""

RESPONSE2=$(curl -s http://localhost:11434/api/chat -d "{
  \"model\": \"$MODEL\",
  \"messages\": [
    {\"role\": \"user\", \"content\": \"Search the web for recent AI news\"}
  ],
  \"tools\": [
    {
      \"type\": \"function\",
      \"function\": {
        \"name\": \"web_search\",
        \"description\": \"Search the web for information\",
        \"parameters\": {
          \"type\": \"object\",
          \"properties\": {
            \"query\": {
              \"type\": \"string\",
              \"description\": \"The search query\"
            }
          },
          \"required\": [\"query\"]
        }
      }
    }
  ],
  \"stream\": false
}")

if echo "$RESPONSE2" | grep -q "tool_calls"; then
  echo "   ✅ Model generated tool call"
  TOOL_NAME2=$(echo "$RESPONSE2" | jq -r '.message.tool_calls[0].function.name' 2>/dev/null)
  TOOL_ARGS2=$(echo "$RESPONSE2" | jq -r '.message.tool_calls[0].function.arguments' 2>/dev/null)
  echo "   Tool: $TOOL_NAME2"
  echo "   Args: $TOOL_ARGS2"
else
  echo "   ⚠️  No tool call generated"
  echo "   Response: $(echo "$RESPONSE2" | jq -r '.message.content' 2>/dev/null | head -c 100)"
fi
echo ""

# Test 3: Calendar event
echo "5. Test 3: Calendar Event Tool"
echo "   Query: 'Schedule a meeting tomorrow at 2pm'"
echo ""

RESPONSE3=$(curl -s http://localhost:11434/api/chat -d "{
  \"model\": \"$MODEL\",
  \"messages\": [
    {\"role\": \"user\", \"content\": \"Schedule a meeting with the team tomorrow at 2pm\"}
  ],
  \"tools\": [
    {
      \"type\": \"function\",
      \"function\": {
        \"name\": \"create_calendar_event\",
        \"description\": \"Create a calendar event\",
        \"parameters\": {
          \"type\": \"object\",
          \"properties\": {
            \"title\": {\"type\": \"string\", \"description\": \"Event title\"},
            \"start_time\": {\"type\": \"string\", \"description\": \"Start time\"}
          },
          \"required\": [\"title\", \"start_time\"]
        }
      }
    }
  ],
  \"stream\": false
}")

if echo "$RESPONSE3" | grep -q "tool_calls"; then
  echo "   ✅ Model generated tool call"
  TOOL_NAME3=$(echo "$RESPONSE3" | jq -r '.message.tool_calls[0].function.name' 2>/dev/null)
  echo "   Tool: $TOOL_NAME3"
else
  echo "   ⚠️  No tool call generated"
fi
echo ""

# Test 4: Reminder
echo "6. Test 4: Reminder Tool"
echo "   Query: 'Remind me to call mom in 1 hour'"
echo ""

RESPONSE4=$(curl -s http://localhost:11434/api/chat -d "{
  \"model\": \"$MODEL\",
  \"messages\": [
    {\"role\": \"user\", \"content\": \"Remind me to call mom in 1 hour\"}
  ],
  \"tools\": [
    {
      \"type\": \"function\",
      \"function\": {
        \"name\": \"create_reminder\",
        \"description\": \"Create a reminder\",
        \"parameters\": {
          \"type\": \"object\",
          \"properties\": {
            \"task\": {\"type\": \"string\", \"description\": \"What to be reminded about\"},
            \"time\": {\"type\": \"string\", \"description\": \"When to be reminded\"}
          },
          \"required\": [\"task\", \"time\"]
        }
      }
    }
  ],
  \"stream\": false
}")

if echo "$RESPONSE4" | grep -q "tool_calls"; then
  echo "   ✅ Model generated tool call"
  TOOL_NAME4=$(echo "$RESPONSE4" | jq -r '.message.tool_calls[0].function.name' 2>/dev/null)
  echo "   Tool: $TOOL_NAME4"
else
  echo "   ⚠️  No tool call generated"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Model: $MODEL"
echo ""
echo "Tool Calling Support:"
if echo "$RESPONSE$RESPONSE2$RESPONSE3$RESPONSE4" | grep -q "tool_calls"; then
  echo "  ✅ Model can generate tool calls"
else
  echo "  ⚠️  Model did not generate tool calls"
  echo "  This could mean:"
  echo "  - Model doesn't support tools well"
  echo "  - Tool definitions need adjustment"
  echo "  - Try qwen2.5:7b-instruct for better support"
fi
echo ""
echo "Available Tools:"
echo "  1. get_weather - Get current weather"
echo "  2. web_search - Search the web"
echo "  3. create_calendar_event - Create calendar events"
echo "  4. create_reminder - Create reminders"
echo ""
echo "Next Steps:"
echo "  1. Configure API keys in .env for real tool execution"
echo "  2. Start server: npm start"
echo "  3. Test with voice: Ask about weather, search, etc."
echo "  4. Check server logs for tool execution"
echo ""

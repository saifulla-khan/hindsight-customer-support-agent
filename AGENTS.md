# Agent Guide: Hindsight Support Agent

This document provides context and guidance for AI agents working with this codebase. It documents non-obvious patterns, gotchas, and essential knowledge that isn't immediately apparent from reading individual files.

## Project Overview

This is a **Python-based customer support agent with Hindsight Cloud memory integration**. It uses Streamlit for the frontend, OpenRouter API for LLM inference (DeepSeek models), and Hindsight Cloud (`api.hindsight.vectorize.io`) for persistent customer memory storage.

## Architecture & Flow

### Dual-Bank Memory System
The agent uses **two separate memory banks**:
1. **Customer-specific bank** (`customer_id`): Stores individual customer history, preferences, and past tickets
2. **Global shared bank** (`global_product_learnings`): Stores technical bug resolutions and learnings across all customers

### Cognitive Loop
1. **Recall**: Query Hindsight Cloud for relevant memories based on customer query
2. **Reason**: Generate response using DeepSeek LLM with recalled context injected into system prompt
3. **Retain**: Store the interaction back to Hindsight Cloud for future recall

## Essential Commands

### Setup & Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (copy .env.example if exists)
cp .env.example .env  # Then edit with your API keys
```

### Running the Application
```bash
# Start Streamlit frontend
streamlit run app.py

# Test the agent directly
python test_agent.py

# Seed initial memories to Hindsight Cloud
python seed_hindsight.py
```

### Development Testing
```bash
# Run the test suite
python test_agent.py
```

## Configuration Files

### `.env` Configuration
**Critical**: The `.env` file **must** contain:
- `OPENROUTER_API_KEY`: API key for OpenRouter (DeepSeek models)
- `HINDSIGHT_API_KEY`: API key for Hindsight Cloud
- `HINDSIGHT_BANK_ID`: Default bank ID (`customer_support`)
- `HINDSIGHT_API_URL`: API endpoint (`https://api.hindsight.vectorize.io`)

### `.crushrc` Configuration
This is a **Bash script** that:
1. Loads environment variables from `.env`
2. Configures OpenRouter as a provider with API key
3. Sets up DeepSeek v3.2 as the default model with reasoning capabilities

## Key Files & Their Purposes

### Core Application
- `app.py`: Streamlit frontend with customer personas and memory inspector
- `agent.py`: Core support agent logic with Hindsight integration
- `test_agent.py`: Test scenarios for the agent
- `seed_hindsight.py`: Script to seed initial memories to Hindsight Cloud
- `seed_data.json`: Synthetic customer data for seeding

### Configuration & Documentation
- `blueprint.txt`: Comprehensive architectural specification
- `Customer_Support_Agent_Blueprint.pdf`: Detailed PDF documentation

## Code Patterns & Conventions

### Memory Integration Pattern
The `agent.py` follows this exact pattern for memory operations:
```python
# 1. Recall personal context
personal_recall = hindsight_client.recall(bank_id=customer_id, query=user_message)

# 2. Recall global context  
global_recall = hindsight_client.recall(bank_id="global_product_learnings", query=user_message)

# 3. Parse responses using parse_hindsight_recall()
# 4. Inject into system prompt
# 5. Generate LLM response
# 6. Retain interaction
```

### Response Object Structure
The `generate_support_reply()` function returns a rich dictionary:
```python
{
    "reply": "Generated response text",
    "memory_used": True/False,
    "recalled_context": "Formatted memory string",
    "recalled_items": ["list", "of", "raw", "memories"],
    "global_recalled_context": "Global memories string",
    "global_recalled_items": ["global", "memory", "items"],
    "retained": True/False,
    "retained_payload": {"customer_id": "interaction summary"},
    "customer_id": "original customer ID",
    "model": "deepseek/deepseek-chat",
    "thinking_trace": "Reasoning trace if available",
    "recall_ms": 123,  # milliseconds for recall
    "llm_ms": 456,     # milliseconds for LLM
    "active_banks": ["list", "of", "banks", "used"]
}
```

### Customer Personas
Three pre-defined customer personas in `app.py`:
- `cust_001`: Alex Johnson - Senior Developer, Enterprise tier, Linux CLI preference
- `cust_002`: Maria Chen - Operations Lead, Enterprise billing, recent seat upgrade
- `cust_003`: David Okafor - Small business owner, Starter plan, needs non-technical steps

## Important Gotchas

### 1. API Key Management
- **Never commit `.env`** with actual API keys
- The `.crushrc` loads environment variables **before** configuring providers
- Missing API keys cause immediate `ValueError` in `agent.py`

### 2. Hindsight Client Version
- Uses `hindsight-client>=1.2.0`
- Response parsing (`parse_hindsight_recall`) handles multiple response formats:
  - `results` attribute
  - `memories` attribute
  - Direct list/dict responses
  - String responses

### 3. OpenRouter Configuration
- Uses `openai` package with `base_url="https://openrouter.ai/api/v1"`
- Supports reasoning with `extra_body={"reasoning": {"effort": "medium"}}`
- Falls back gracefully if reasoning not supported

### 4. Memory Toggle Behavior
When `use_memory=False`:
- Bypasses all Hindsight calls
- Uses generic stateless prompt
- No retention occurs
- Response still returns dictionary but with memory flags set to False

### 5. Global Memory Retention
Technical keywords in user messages trigger retention to global bank:
- `["bug", "fix", "workaround", "patch", "issue", "error", "crash", "solution"]`
- Creates stripped summary (`user_message[:200]...`)

## Testing Patterns

### Test Scenarios
`test_agent.py` tests three scenarios:
1. Generic password reset (`cust_003`) - tests fallback behavior
2. Login failing after password reset (`cust_001`) - tests personal memory recall
3. PDF download stuck (`cust_001`) - tests cross-ticket memory

### Error Handling in Tests
Tests include graceful fallback for missing API keys:
- Prints mock response instead of crashing
- Provides clear instructions for setting up `.env`

## Streamlit UI Patterns

### Session State Management
The app maintains multiple session state variables:
- `chat_histories`: Per-customer chat history
- `last_inspector_state`: Last Hindsight inspector data
- `memories_retained_count`: Counter for retained memories
- `approved_messages`: Track approved replies

### Two-Column Layout
- **Left column**: Live chat with customer persona selection
- **Right column**: Hindsight memory inspector with raw context display

### Memory Inspector
Shows:
- Raw recalled context as markdown code block
- Individual memory cards with numbering
- Retention status (success/failure)
- Active memory banks used

## Development Notes

### Adding New Customer Personas
1. Add to `PERSONAS` dictionary in `app.py`
2. Include `name`, `role`, `sample_prompt`, `icon`
3. Add corresponding seed data to `seed_data.json`
4. Update `seed_hindsight.py` if adding new memory banks

### Modifying Memory Logic
- Changes to `parse_hindsight_recall()` affect both prompt injection AND UI display
- Global memory bank name is hardcoded as `"global_product_learnings"`
- Customer IDs must match between `PERSONAS` and seed data

### Performance Considerations
- Recalls from two banks happen sequentially (could be parallelized)
- Latency metrics (`recall_ms`, `llm_ms`) are tracked for debugging
- Technical keyword scanning is case-insensitive

## Common Issues & Solutions

### "Missing required environment variables"
**Solution**: Ensure `.env` exists with all required keys:
```bash
OPENROUTER_API_KEY=your_openrouter_key
HINDSIGHT_API_KEY=your_hindsight_key
HINDSIGHT_BANK_ID=customer_support
HINDSIGHT_API_URL=https://api.hindsight.vectorize.io
```

### "Hindsight recall error" in UI
**Solution**:
1. Check Hindsight API key validity
2. Verify `seed_hindsight.py` ran successfully
3. Confirm bank IDs match between code and seeded data

### Streamlit not updating chat history
**Solution**: Use `st.rerun()` after modifying session state. The app already does this correctly.

### Memory inspector shows "No context returned"
**Solution**: 
1. Ensure memory toggle is ON (green badge should show)
2. Send a message to trigger recall
3. Check network connectivity to Hindsight API

## Security Considerations

### API Key Protection
- Never log API keys
- `.env` is gitignored (check `.gitignore`)
- Keys only used for authenticated API calls

### Customer Data
- Customer IDs are synthetic (`cust_001`, etc.)
- No real PII in seed data
- Memory banks are isolated per customer

## Deployment Notes

### Environment Setup
1. Python 3.10+ required
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` with production API keys
4. Seed initial memories: `python seed_hindsight.py`

### Scaling Considerations
- Each customer gets isolated memory bank
- Global bank shared across all customers
- Streamlit may need scaling for concurrent users
- Consider adding Redis for session persistence

## References

### External Services
- **OpenRouter**: `https://openrouter.ai` (DeepSeek models)
- **Hindsight Cloud**: `https://api.hindsight.vectorize.io`
- **Streamlit**: Frontend framework

### Key Documentation
- `blueprint.txt`: Detailed architecture specification
- `Customer_Support_Agent_Blueprint.pdf`: Complete project blueprint
- This file (`AGENTS.md`): Agent-focused guide

---

*Last Updated: Based on codebase analysis completed 2026-11-07*
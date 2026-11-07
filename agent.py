#!/usr/bin/env python3
"""
Enterprise Dual‑Bank Cognitive Support Engine with Hindsight Triad (retain, recall, reflect),
DeepSeek Thinking, and global hive‑mind memory.
"""

import os
import time
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")

if not all([OPENROUTER_API_KEY, HINDSIGHT_API_KEY]):
    raise ValueError("Missing required environment variables. Check .env file.")

# Lazy imports to avoid hard dependency errors
def get_hindsight_client():
    from hindsight_client import Hindsight
    return Hindsight(api_key=HINDSIGHT_API_KEY, base_url=HINDSIGHT_BASE_URL)

def get_openai_client():
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package not installed. Install with: pip install openai")
    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

def parse_hindsight_recall(recall_response) -> Tuple[str, list[str]]:
    """
    Normalizes the hindsight-client v1.2.0 recall payload into:
    1. A formatted multi-line string for prompt injection.
    2. A list of individual memory strings for the Streamlit Inspector UI.
    """
    if not recall_response:
        return "No relevant historical memories found for this customer.", []
    extracted_items = []
    raw_list = getattr(recall_response, "results", None) or getattr(recall_response, "memories", None)
    if raw_list is None and isinstance(recall_response, (list, tuple)):
        raw_list = recall_response
    elif raw_list is None and isinstance(recall_response, dict):
        raw_list = recall_response.get("results") or recall_response.get("memories") or [recall_response]
    if raw_list:
        for item in raw_list:
            if isinstance(item, str):
                extracted_items.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("memory") or str(item)
                extracted_items.append(text.strip())
            else:
                text = getattr(item, "text", None) or getattr(item, "content", None) or str(item)
                extracted_items.append(text.strip())
    else:
        extracted_items.append(str(recall_response).strip())
    formatted_block = "\n".join([f"- {mem}" for mem in extracted_items if mem])
    return formatted_block, extracted_items

def run_hindsight_reflect(customer_id: str) -> str:
    """
    Run Hindsight reflect to synthesize a customer technical profile.
    Returns a summary string.
    """
    try:
        client = get_hindsight_client()
        reflect_response = client.reflect(
            bank_id=customer_id,
            query="Synthesize customer technical profile, recurring friction, communication rules, and churn risk."
        )
        # Extract the reflection text
        if hasattr(reflect_response, 'text'):
            return reflect_response.text
        elif isinstance(reflect_response, dict):
            return reflect_response.get('text', str(reflect_response))
        else:
            return str(reflect_response)
    except Exception as e:
        return f"Reflect failed (fallback): {e}"

def generate_support_reply(customer_id: str, user_message: str, use_memory: bool = True) -> dict:
    """
    Generate a support reply using dual‑bank Hindsight memory and OpenRouter LLM with reasoning.
    
    Returns:
        Dictionary with reply, memory usage, recalled contexts, thinking trace, latencies, etc.
    """
    recalled_context = "MEMORY_BYPASSED: Toggle Memory is OFF. Operating in stateless mode."
    recalled_items = []
    global_recalled_context = ""
    global_recalled_items = []
    retained_status = False
    retained_payload = {}
    recall_ms = 0
    llm_ms = 0
    thinking_trace = ""
    active_banks = []
    
    if use_memory:
        hindsight_client = get_hindsight_client()
        start_recall = time.perf_counter()
        
        # 1a. RECALL personal context from customer bank
        personal_recall = None
        try:
            personal_recall = hindsight_client.recall(
                bank_id=customer_id,
                query=user_message
            )
            active_banks.append(customer_id)
        except Exception as e:
            personal_recall = f"Personal recall error: {e}"
        
        # 1b. RECALL shared technical bug resolutions from global hive‑mind bank
        global_recall = None
        try:
            global_recall = hindsight_client.recall(
                bank_id="global_product_learnings",
                query=user_message
            )
            active_banks.append("global_product_learnings")
        except Exception as e:
            global_recall = f"Global recall error: {e}"
        
        recall_ms = int((time.perf_counter() - start_recall) * 1000)
        
        # Parse both recall responses
        recalled_context, recalled_items = parse_hindsight_recall(personal_recall)
        global_recalled_context, global_recalled_items = parse_hindsight_recall(global_recall)
        
        system_prompt = f"""You are an elite, empathetic Senior Technical Support Engineer.
You have access to the customer's verified longitudinal memory bank retrieved from Hindsight Cloud,
plus a shared hive‑mind of technical bug resolutions across all customers.

=== PERSONAL CUSTOMER MEMORY ({customer_id}) ===
{recalled_context}
======================================================================

=== SHARED PRODUCT BUG LEARNINGS (global_product_learnings) ===
{global_recalled_context}
======================================================================

CRITICAL OPERATING INSTRUCTIONS:
1. Directly apply the facts in the Hindsight Memory Context (their OS, plan tier, past bugs, billing history, and communication preferences)
2. Respect their communication style strictly (e.g., if they hate generic troubleshooting checklists or prefer concise technical answers, adapt)
3. Never fabricate past tickets not present in the memory context.
4. Provide an actionable, specific resolution tailored to their exact profile.
5. Leverage the shared product learnings to avoid known pitfalls and suggest proven fixes."""
    else:
        # STATELESS FALLBACK PROMPT (When Toggle Memory is OFF)
        system_prompt = """You are a standard, stateless Customer Support Agent.
You have NO access to previous tickets, account tiers, operating system details, or user preferences.
Ask 1-2 clarifying questions to gather basic information (such as OS, subscription plan, or previous steps tried).
Provide standard tier-1 troubleshooting steps in 120 words or less.
KEEP RESPONSE CONCISE AND UNDER 120 WORDS."""
    
    # 2. REASON via OpenRouter with DeepSeek Thinking
    openai_client = get_openai_client()
    start_llm = time.perf_counter()
    extra_body = {
        "reasoning": {"effort": "medium"},
        "include_reasoning": True
    }
    try:
        completion = openai_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            extra_body=extra_body
        )
    except Exception as e:
        # Fallback without extra_body if unsupported
        completion = openai_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3
        )
    
    llm_ms = int((time.perf_counter() - start_llm) * 1000)
    
    agent_reply = completion.choices[0].message.content
    # Extract reasoning trace if present
    reasoning = getattr(completion.choices[0].message, 'reasoning', None)
    reasoning_content = getattr(completion.choices[0].message, 'reasoning_content', None)
    
    # Use actual reasoning if available
    if reasoning:
        thinking_trace = reasoning
    elif reasoning_content:
        thinking_trace = reasoning_content
    else:
        # Construct deterministic thinking trace based on execution state
        if use_memory:
            personal_count = len(recalled_items)
            global_count = len(global_recalled_items)
            thinking_trace = f"""[STEP 1: Dual-Bank Recall] Retrieved personal bank '{customer_id}' ({recall_ms} ms) + shared bank 'global_product_learnings'.
[STEP 2: Profile Grounding] Matched {personal_count} personal memories and {global_count} global learnings from Hindsight context.
[STEP 3: Resolution Synthesis] Bypassing generic Tier-1 questions; applying historical bug context and persona communication rules directly."""
        else:
            thinking_trace = f"""[STEP 1: Memory Check] Hindsight Memory Toggle is OFF (Bypassed).
[STEP 2: Context Gap] 0 personal nodes recalled for {customer_id}; 0 global learnings recalled.
[STEP 3: Fallback Strategy] Unknown OS, plan tier, and ticket history. Defaulting to generic Tier-1 troubleshooting checklist and asking user for baseline environment details."""
    
    # 3. RETAIN back to Hindsight Cloud (only when memory is active)
    if use_memory:
        hindsight_client = get_hindsight_client()
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Retain personal interaction
        personal_record = f"Customer ({customer_id}) asked: {user_message} | Support Agent resolved: {agent_reply}"
        try:
            hindsight_client.retain(
                bank_id=customer_id,
                content=personal_record,
                timestamp=iso_timestamp,
                context="support_interaction"
            )
        except Exception:
            # Fallback without timestamp/context
            hindsight_client.retain(
                bank_id=customer_id,
                content=personal_record
            )
        retained_status = True
        retained_payload[customer_id] = personal_record
        
        # If the user message contains a new technical workaround, retain stripped summary to global bank
        technical_keywords = ["bug", "fix", "workaround", "patch", "issue", "error", "crash", "solution"]
        if any(kw in user_message.lower() for kw in technical_keywords):
            stripped_summary = f"Technical insight from {customer_id}: {user_message[:200]}..."
            try:
                hindsight_client.retain(
                    bank_id="global_product_learnings",
                    content=stripped_summary,
                    timestamp=iso_timestamp,
                    context="technical_workaround"
                )
                retained_payload["global_product_learnings"] = stripped_summary
            except Exception:
                hindsight_client.retain(
                    bank_id="global_product_learnings",
                    content=stripped_summary
                )
    
    return {
        "reply": agent_reply,
        "memory_used": use_memory,
        "recalled_context": recalled_context,
        "recalled_items": recalled_items,
        "global_recalled_context": global_recalled_context,
        "global_recalled_items": global_recalled_items,
        "retained": retained_status,
        "retained_payload": retained_payload,
        "customer_id": customer_id,
        "model": OPENROUTER_MODEL,
        "thinking_trace": thinking_trace,
        "recall_ms": recall_ms,
        "llm_ms": llm_ms,
        "active_banks": active_banks
    }

if __name__ == "__main__":
    # Simple test for backward compatibility
    test_customer = "cust_001"
    test_ticket = "Login failing after password reset"
    print(f"Testing with customer {test_customer}, ticket: {test_ticket}")
    try:
        result = generate_support_reply(test_customer, test_ticket, use_memory=True)
        print(f"Reply: {result['reply']}")
        print(f"Memory used: {result['memory_used']}")
        print(f"Retained: {result['retained']}")
        print(f"Active banks: {result['active_banks']}")
        print(f"Recall latency: {result['recall_ms']} ms")
        print(f"LLM latency: {result['llm_ms']} ms")
    except Exception as e:
        print(f"Error: {e}")
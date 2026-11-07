#!/usr/bin/env python3
"""
Test the support agent with three scenarios.
"""

import sys
sys.path.insert(0, '.')

from agent import generate_support_reply

def run_scenario(customer_id, ticket_text, description):
    print(f"\n--- {description} ---")
    print(f"Customer: {customer_id}")
    print(f"Ticket: '{ticket_text}'")
    try:
        result = generate_support_reply(customer_id, ticket_text, use_memory=True)
        # Handle both dict (new) and str (old) return types
        if isinstance(result, dict):
            reply = result["reply"]
            memory_used = result["memory_used"]
            retained = result["retained"]
            print(f"Agent Reply:\n{reply}")
            print(f"Memory used: {memory_used}, Retained: {retained}")
        else:
            # Legacy string return
            print(f"Agent Reply:\n{result}")
            print("Note: agent.py returned string instead of dict.")
    except Exception as e:
        print(f"ERROR: {e}")
        # Provide mock response for demonstration if API keys missing
        if "API key" in str(e) or "authentication" in str(e):
            print("NOTE: API keys missing or invalid. Set OPENROUTER_API_KEY and HINDSIGHT_API_KEY in .env")
            print("Mock reply: Please check your browser cache and try again.")

if __name__ == "__main__":
    print("Testing Support Agent with Hindsight Memory")
    print("=" * 50)
    
    # Scenario 1: cust_003 asks generic password reset
    run_scenario(
        "cust_003",
        "How do I reset my password?",
        "Scenario 1: Generic password reset (no memory)"
    )
    
    # Scenario 2: cust_001 asks about login failing after password reset
    run_scenario(
        "cust_001",
        "Login failing after password reset",
        "Scenario 2: Memory recall for cust_001 (cache clearing)"
    )
    
    # Scenario 3: cust_001 asks about PDF download stuck
    run_scenario(
        "cust_001",
        "PDF download stuck",
        "Scenario 3: Cross-ticket memory for cust_001 (ad-blockers)"
    )
    
    print("\n" + "=" * 50)
    print("Test scenarios completed.")
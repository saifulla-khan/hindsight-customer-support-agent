#!/usr/bin/env python3
"""
Seed Hindsight memory bank with synthetic customer support data.
Creates separate memory banks for each customer (cust_001, cust_002, cust_003).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_API_URL = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io")

if not HINDSIGHT_API_KEY:
    print("ERROR: HINDSIGHT_API_KEY not found in .env")
    exit(1)

# Load seed data
seed_path = Path(__file__).parent / "seed_data.json"
with open(seed_path, "r") as f:
    customers = json.load(f)

print(f"Loaded {len(customers)} customers")

# Import Hindsight SDK
from hindsight_client import Hindsight

# Initialize client
client = Hindsight(api_key=HINDSIGHT_API_KEY, base_url=HINDSIGHT_API_URL)

total_memories = 0
successful_banks = 0

for customer in customers:
    customer_id = customer["customer_id"]
    name = customer["name"]
    plan = customer["plan"]
    memories = []
    
    for ticket in customer["past_tickets"]:
        ticket_text = ticket["ticket_text"]
        resolution = ticket["resolution"]
        # Create a memory string
        content = f"Customer {name} ({customer_id}, {plan}) reported: '{ticket_text}'. Resolution: {resolution}."
        memory = {
            "type": "text",
            "text": content,
            "metadata": {
                "customer_id": customer_id,
                "name": name,
                "plan": plan,
                "ticket_text": ticket_text,
                "resolution": resolution,
                "worked": ticket.get("worked", True)
            }
        }
        memories.append(memory)
    
    # Retain batch to customer-specific bank
    if memories:
        try:
            response = client.retain(bank_id=customer_id, content=memories)
            print(f"✓ Retained {len(memories)} memories for {name} (bank '{customer_id}')")
            total_memories += len(memories)
            successful_banks += 1
        except Exception as e:
            print(f"✗ Failed to retain memories for {customer_id}: {e}")
    else:
        print(f"⚠ No memories to seed for {customer_id}")

print(f"\nSummary:")
print(f"  • Created {successful_banks} customer memory banks")
print(f"  • Seeded {total_memories} total memories")
print(f"  • Banks ready: cust_001, cust_002, cust_003")
print("\nRun the Streamlit app with: streamlit run app.py")
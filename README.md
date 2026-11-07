# 🧠 Hindsight Cognitive Customer Support Agent

An enterprise-grade, dual-bank AI Customer Support Agent built to solve **Session Amnesia**. 

Traditional AI support bots treat every customer interaction as an isolated event. This project integrates **Hindsight Cloud** as a persistent memory layer, allowing the agent to remember a customer's technical environment, subscription tier, and past resolutions across multiple sessions.

## 🚀 The Core Problem
Support teams lose hours re-reading past tickets, and customers get frustrated repeating themselves. This agent uses a **Recall -> Reason -> Retain** loop to pull exact historical context from Hindsight Cloud, inject it into the LLM prompt, and save the new interaction back to the cloud for future use.

## 🏗️ System Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer (Streamlit UI)
    participant App as app.py (UI State)
    participant Agent as agent.py (Orchestrator)
    participant HS as Hindsight Cloud (api.hindsight.vectorize.io)
    participant LLM as OpenRouter (DeepSeek)

    User->>App: Selects Persona (e.g., cust_001) & Sends Message
    App->>Agent: generate_support_reply(customer_id, message, use_memory)
    alt Toggle Memory == ON
        Agent->>HS: hindsight.recall(bank_id=customer_id, query=message)
        HS-->>Agent: Returns historical facts & preferences (memory_context)
        Agent->>LLM: System Prompt + [memory_context] + User Message
        LLM-->>Agent: Personalized Support Resolution
        Agent->>HS: hindsight.retain(bank_id=customer_id, content=turn_summary)
        HS-->>Agent: 200 OK (Memory Retained)
    else Toggle Memory == OFF
        Agent->>LLM: Generic Stateless Prompt + User Message
        LLM-->>Agent: Generic Tier-1 Troubleshooting Reply
    end
    Agent-->>App: Returns {reply, recalled_context, retained}
    App-->>User: Renders Chat Bubble + Raw Hindsight Inspector Panel

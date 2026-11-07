import streamlit as st
from agent import generate_support_reply, run_hindsight_reflect

st.set_page_config(
    page_title="Hindsight Support | AI Customer Memory",
    page_icon="🧠",
    layout="wide"
)

# ============ CUSTOM CSS FOR PREMIUM UI ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    .main .block-container {
        padding-top: 2rem;
        max-width: 95%;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    /* Chat bubbles */
    .stChatMessage {
        border-radius: 20px !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 1rem !important;
        border: 1px solid #334155 !important;
    }
    
    .stChatMessage[data-testid="user"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        margin-left: 20% !important;
        border: none !important;
    }
    
    .stChatMessage[data-testid="assistant"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #cbd5e1 !important;
        margin-right: 20% !important;
        border: 1px solid #475569 !important;
    }
    
    /* Chat input glow */
    .stChatInput input {
        background: rgba(30, 41, 59, 0.9) !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3) !important;
        transition: box-shadow 0.3s ease !important;
    }
    
    .stChatInput input:focus {
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.6) !important;
        border-color: #3b82f6 !important;
    }
    
    /* Cards */
    .memory-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .memory-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3);
    }
    
    /* Metric */
    .metric-box {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #475569;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .approve-btn {
        background: linear-gradient(135deg, #10b981 0%, #047857 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    .edit-btn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    /* Divider */
    hr {
        border-color: #475569 !important;
        margin: 1.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

PERSONAS = {
    "cust_001": {
        "name": "Alex (cust_001)",
        "role": "Senior Developer • Pro/Enterprise Tier • Linux CLI Preference",
        "sample_prompt": "The export issue is happening again. How do I fix it?",
        "icon": "💻"
    },
    "cust_002": {
        "name": "Maria (cust_002)",
        "role": "Operations Lead • Enterprise Billing • Recent Seat Upgrade",
        "sample_prompt": "Just checking in on my upcoming invoice—is everything sorted out from last week?",
        "icon": "📊"
    },
    "cust_003": {
        "name": "David (cust_003)",
        "role": "Small Business Owner • Starter Plan • Needs Non-Technical Steps",
        "sample_prompt": "I'm locked out of the dashboard settings again and don't know where to click.",
        "icon": "👔"
    }
}

# ============ SESSION STATE INIT ============
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {cid: [] for cid in PERSONAS}
if "last_inspector_state" not in st.session_state:
    st.session_state.last_inspector_state = {cid: None for cid in PERSONAS}
if "memories_retained_count" not in st.session_state:
    st.session_state.memories_retained_count = 0
if "approved_messages" not in st.session_state:
    st.session_state.approved_messages = {}  # key: (cid, msg_idx) -> True
if "reflect_results" not in st.session_state:
    st.session_state.reflect_results = {cid: None for cid in PERSONAS}
if "editing_message" not in st.session_state:
    st.session_state.editing_message = None  # Format: (cid, idx)

# ============ HEADER WITH METRICS ============
col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
with col_header1:
    st.title("🧠 Hindsight Support Agent")
    st.caption("Enterprise‑grade AI support with persistent customer memory")
with col_header2:
    st.metric(
        label="Memories Retained This Session",
        value=st.session_state.memories_retained_count,
        delta=None
    )
with col_header3:
    pass

# ============ CONTROL BAR ============
ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.2, 1.2, 0.6])
with ctrl_col1:
    selected_cid = st.selectbox(
        "Select Customer Persona:",
        options=list(PERSONAS.keys()),
        format_func=lambda cid: f"{PERSONAS[cid]['icon']} {PERSONAS[cid]['name']} — {PERSONAS[cid]['role']}"
    )
with ctrl_col2:
    st.write("")
    use_memory = st.toggle("Hindsight Memory", value=True)
with ctrl_col3:
    st.write("")
    if st.button("🔄 Reset UI Chat", use_container_width=True):
        st.session_state.chat_histories[selected_cid] = []
        st.session_state.last_inspector_state[selected_cid] = None
        st.rerun()

st.divider()

# ============ MAIN TWO‑COLUMN LAYOUT ============
col_chat, col_memory = st.columns([1.15, 0.85], gap="large")

# ============ LEFT COLUMN: CHAT ============
with col_chat:
    # Add compact/full-height toggle
    compact_toggle_col1, compact_toggle_col2 = st.columns([0.8, 0.2])
    with compact_toggle_col1:
        st.subheader(f"{PERSONAS[selected_cid]['icon']} Live Support Session")
    with compact_toggle_col2:
        compact_view = st.toggle("📄 Compact View", value=False, help="Toggle between compact (650px) and full-height chat view")
    
    chat_height = 650 if compact_view else None
    
    st.caption(f"💡 Try: *\"{PERSONAS[selected_cid]['sample_prompt']}\"*")
    
    chat_container = st.container(height=chat_height if chat_height is not None else "content", border=True)
    with chat_container:
        history = st.session_state.chat_histories[selected_cid]
        if not history:
            st.info("No messages yet. Send a message to start the conversation.")
        else:
            for idx, msg in enumerate(history):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
                    # Check if this message is being edited
                    if st.session_state.editing_message == (selected_cid, idx):
                        # Show inline editor
                        edited_content = st.text_area(
                            "Edit Assistant Reply:",
                            value=msg["content"],
                            height=200,
                            key=f"editor_{selected_cid}_{idx}"
                        )
                        
                        # Save and retain edited reply
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            if st.button(f"💾 Save & Retain Edited Reply", key=f"save_{selected_cid}_{idx}", use_container_width=True):
                                # Update message content
                                st.session_state.chat_histories[selected_cid][idx]["content"] = edited_content
                                
                                # If memory is enabled, retain the human-corrected resolution
                                if use_memory:
                                    from agent import get_hindsight_client
                                    from datetime import datetime
                                    from datetime import timezone
                                    
                                    hindsight_client = get_hindsight_client()
                                    iso_timestamp = datetime.now(timezone.utc).isoformat()
                                    
                                    # Get the user message that prompted this reply
                                    user_msg = ""
                                    if idx > 0 and st.session_state.chat_histories[selected_cid][idx-1]["role"] == "user":
                                        user_msg = st.session_state.chat_histories[selected_cid][idx-1]["content"]
                                    
                                    personal_record = f"Customer ({selected_cid}) asked: {user_msg} | Human-Edited Support Agent resolved: {edited_content}"
                                    try:
                                        hindsight_client.retain(
                                            bank_id=selected_cid,
                                            content=personal_record,
                                            timestamp=iso_timestamp,
                                            context="human_corrected_support_interaction"
                                        )
                                    except Exception:
                                        hindsight_client.retain(
                                            bank_id=selected_cid,
                                            content=personal_record
                                        )
                                
                                # Clear editing state
                                st.session_state.editing_message = None
                                st.success("✅ Human-edited reply saved & retained to Hindsight Cloud!")
                                st.rerun()
                        
                        with edit_col2:
                            if st.button(f"❌ Cancel", key=f"cancel_{selected_cid}_{idx}", use_container_width=True):
                                st.session_state.editing_message = None
                                st.rerun()
                        
                        # Don't show approval/edit buttons while editing
                        continue
                    
                    if msg["role"] == "assistant":
                        # Memory badge
                        badge = "🟢 Hindsight Memory ON" if msg.get("memory_used") else "⚪ Stateless Mode"
                        st.caption(badge)
                        
                        # Approve/Edit buttons (only for assistant messages)
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button(f"✅ Approve Reply", key=f"approve_{selected_cid}_{idx}", use_container_width=True):
                                st.session_state.approved_messages[(selected_cid, idx)] = True
                                st.toast("✅ Reply approved and sent to customer!", icon="✅")
                                st.rerun()
                        with col_btn2:
                            # Edit button with inline editor
                            edit_key = f"edit_{selected_cid}_{idx}"
                            if st.button(f"✏️ Edit Draft", key=edit_key, use_container_width=True):
                                # Start editing this message
                                st.session_state.editing_message = (selected_cid, idx)
                                st.rerun()
                        
                        # Show approval status
                        if st.session_state.approved_messages.get((selected_cid, idx), False):
                            st.success("✅ Approved and sent")
    
    
    # Quick-Fire Demo Buttons
    demo_col1, demo_col2, demo_col3 = st.columns(3)
    with demo_col1:
        if st.button("🐛 Trigger Known Issue (Test Recall)", use_container_width=True, help="Tests memory recall with a known issue"):
            test_query = "Login failing after password reset"
            if selected_cid == "cust_002":
                test_query = "API rate-limit errors"
            elif selected_cid == "cust_003":
                test_query = "Dashboard charts not updating"
            st.session_state.chat_histories[selected_cid].append({
                "role": "user",
                "content": test_query
            })
            with st.spinner("🌀 Executing Recall → DeepSeek → Retain pipeline..."):
                result = generate_support_reply(
                    customer_id=selected_cid,
                    user_message=test_query,
                    use_memory=use_memory
                )
                if isinstance(result, str):
                    result = {
                        "reply": result,
                        "memory_used": use_memory,
                        "recalled_context": "Agent returned raw string.",
                        "recalled_items": [],
                        "retained": use_memory,
                        "model": "deepseek/deepseek-chat"
                    }
                
                if result.get("retained", False):
                    st.session_state.memories_retained_count += 1
                
                st.session_state.chat_histories[selected_cid].append({
                    "role": "assistant",
                    "content": result["reply"],
                    "memory_used": result.get("memory_used", use_memory)
                })
                st.session_state.last_inspector_state[selected_cid] = result
                st.rerun()
    
    with demo_col2:
        if st.button("💡 Share New Bug Fix (Test Hive-Mind Retain)", use_container_width=True, help="Tests global hive-mind retention"):
            bug_fixes = {
                "cust_001": "Found workaround: Clearing browser cache fixes 90% of login issues",
                "cust_002": "Solution: API rate limits can be bypassed with exponential backoff",
                "cust_003": "Fix: Proxy server caching requires manual dashboard refresh"
            }
            test_query = bug_fixes.get(selected_cid, "Found bug fix in production environment")
            st.session_state.chat_histories[selected_cid].append({
                "role": "user",
                "content": test_query
            })
            with st.spinner("🌀 Executing Recall → DeepSeek → Retain pipeline..."):
                result = generate_support_reply(
                    customer_id=selected_cid,
                    user_message=test_query,
                    use_memory=use_memory
                )
                if isinstance(result, str):
                    result = {
                        "reply": result,
                        "memory_used": use_memory,
                        "recalled_context": "Agent returned raw string.",
                        "recalled_items": [],
                        "retained": use_memory,
                        "model": "deepseek/deepseek-chat"
                    }
                
                if result.get("retained", False):
                    st.session_state.memories_retained_count += 1
                
                st.session_state.chat_histories[selected_cid].append({
                    "role": "assistant",
                    "content": result["reply"],
                    "memory_used": result.get("memory_used", use_memory)
                })
                st.session_state.last_inspector_state[selected_cid] = result
                st.rerun()
    
    with demo_col3:
        if st.button("🔄 Verify Persistence After Reset", use_container_width=True, help="Tests memory persistence after UI reset"):
            # First send a message
            test_query = f"Testing memory persistence for {PERSONAS[selected_cid]['name']}"
            st.session_state.chat_histories[selected_cid].append({
                "role": "user",
                "content": test_query
            })
            with st.spinner("🌀 Executing Recall → DeepSeek → Retain pipeline..."):
                result = generate_support_reply(
                    customer_id=selected_cid,
                    user_message=test_query,
                    use_memory=use_memory
                )
                if isinstance(result, str):
                    result = {
                        "reply": result,
                        "memory_used": use_memory,
                        "recalled_context": "Agent returned raw string.",
                        "recalled_items": [],
                        "retained": use_memory,
                        "model": "deepseek/deepseek-chat"
                    }
                
                if result.get("retained", False):
                    st.session_state.memories_retained_count += 1
                
                st.session_state.chat_histories[selected_cid].append({
                    "role": "assistant",
                    "content": result["reply"],
                    "memory_used": result.get("memory_used", use_memory)
                })
                st.session_state.last_inspector_state[selected_cid] = result
                
                # Now reset UI and test recall
                st.session_state.chat_histories[selected_cid] = []
                st.session_state.last_inspector_state[selected_cid] = None
                
                # Send same query again
                test_query2 = f"Testing memory persistence for {PERSONAS[selected_cid]['name']} - part 2"
                st.session_state.chat_histories[selected_cid].append({
                    "role": "user",
                    "content": test_query2
                })
                with st.spinner("🌀 Testing persistence after reset..."):
                    result2 = generate_support_reply(
                        customer_id=selected_cid,
                        user_message=test_query2,
                        use_memory=use_memory
                    )
                    if isinstance(result2, str):
                        result2 = {
                            "reply": result2,
                            "memory_used": use_memory,
                            "recalled_context": "Agent returned raw string.",
                            "recalled_items": [],
                            "retained": use_memory,
                            "model": "deepseek/deepseek-chat"
                        }
                    
                    st.session_state.chat_histories[selected_cid].append({
                        "role": "assistant",
                        "content": result2["reply"],
                        "memory_used": result2.get("memory_used", use_memory)
                    })
                    st.session_state.last_inspector_state[selected_cid] = result2
                st.rerun()
    
    st.divider()
    user_query = st.chat_input(f"💬 Message support as {PERSONAS[selected_cid]['name']}...")
    if user_query:
        st.session_state.chat_histories[selected_cid].append({
            "role": "user",
            "content": user_query
        })
        with st.spinner("🌀 Executing Recall → DeepSeek → Retain pipeline..."):
            result = generate_support_reply(
                customer_id=selected_cid,
                user_message=user_query,
                use_memory=use_memory
            )
            if isinstance(result, str):
                result = {
                    "reply": result,
                    "memory_used": use_memory,
                    "recalled_context": "Agent returned raw string.",
                    "recalled_items": [],
                    "retained": use_memory,
                    "model": "deepseek/deepseek-chat"
                }
            
            # Increment memory counter if retained
            if result.get("retained", False):
                st.session_state.memories_retained_count += 1
            
            st.session_state.chat_histories[selected_cid].append({
                "role": "assistant",
                "content": result["reply"],
                "memory_used": result.get("memory_used", use_memory)
            })
            st.session_state.last_inspector_state[selected_cid] = result
            st.rerun()

# ============ RIGHT COLUMN: MEMORY INSPECTOR ============
with col_memory:
    st.subheader("📊 Hindsight Memory Inspector")
    if use_memory:
        st.success(f"🟢 **MEMORY ACTIVE** — Querying `api.hindsight.vectorize.io` (`bank_id={selected_cid}`)")
    else:
        st.warning("⚪ **MEMORY BYPASSED** — Using generic stateless prompt.")
    
    inspector_data = st.session_state.last_inspector_state[selected_cid]
    with st.container(height=650, border=True):
        if not inspector_data:
            st.markdown(
                "**⏳ Awaiting Interaction...**\n\n"
                "When you send a message, this panel displays the **raw context** recalled from "
                "Hindsight Cloud before injection into the LLM prompt."
            )
        else:
            # Telemetry row
            telemetry_col1, telemetry_col2, telemetry_col3 = st.columns(3)
            with telemetry_col1:
                st.metric(
                    label="Recall Latency",
                    value=f"{inspector_data.get('recall_ms', 0)} ms",
                    delta=None
                )
            with telemetry_col2:
                st.metric(
                    label="DeepSeek Reason",
                    value=f"{inspector_data.get('llm_ms', 0)} ms",
                    delta=None
                )
            with telemetry_col3:
                banks = inspector_data.get('active_banks', [])
                if banks:
                    st.metric(
                        label="Active Memory Banks",
                        value=", ".join(banks),
                        delta=None
                    )
                else:
                    st.metric(
                        label="Active Memory Banks",
                        value="None",
                        delta=None
                    )
            
            st.divider()
            
            # Box 1: Personal & Global Memory
            st.markdown("#### 🧭 Dual-Bank Memory Context")
            
            # Personal memory
            if inspector_data.get('recalled_context') and inspector_data.get('recalled_context') != "No relevant historical memories found for this customer.":
                st.markdown(f"**Personal Memory ({selected_cid}):**")
                st.code(inspector_data.get('recalled_context', 'No personal memory recalled.'), language="markdown")
            
            # Global memory
            if inspector_data.get('global_recalled_context') and inspector_data.get('global_recalled_context') != "No relevant historical memories found for this customer.":
                st.markdown(f"**Global Hive-Mind Memory (global_product_learnings):**")
                st.code(inspector_data.get('global_recalled_context', 'No global memory recalled.'), language="markdown")
            
            st.divider()
            
            # Box 2: DeepSeek Thinking Trace
            with st.expander("🧠 DeepSeek Thinking Trace (How Memory Was Applied)", expanded=True):
                thinking_trace = inspector_data.get('thinking_trace', 'No reasoning trace available.')
                st.code(thinking_trace, language="markdown")
            
            st.divider()
            
            # Box 3: Hindsight Reflect
            st.markdown("#### 🔮 Customer Mental Model Analysis")
            reflect_col1, reflect_col2 = st.columns([0.7, 0.3])
            with reflect_col1:
                if st.button("Run Hindsight .reflect() (Customer Mental Model)", use_container_width=True, 
                           help="Synthesize customer technical profile, recurring friction, communication rules, and churn risk"):
                    with st.spinner("🔮 Analyzing customer mental model..."):
                        reflect_result = run_hindsight_reflect(selected_cid)
                        st.session_state.reflect_results[selected_cid] = reflect_result
                        st.rerun()
            with reflect_col2:
                if st.session_state.reflect_results.get(selected_cid):
                    st.success("✅ Analysis Ready")
            
            # Display reflect results if available
            if st.session_state.reflect_results.get(selected_cid):
                reflect_result = st.session_state.reflect_results[selected_cid]
                with st.container(border=True):
                    st.markdown("##### Executive Customer Health & Churn Risk Card")
                    st.markdown(f"**Customer:** {PERSONAS[selected_cid]['name']} ({selected_cid})")
                    st.markdown(f"**Role:** {PERSONAS[selected_cid]['role']}")
                    st.divider()
                    st.markdown(reflect_result)
            
            st.divider()
            
            # Retention status
            st.divider()
            st.markdown("#### 💾 Retention Status")
            if inspector_data.get("retained"):
                st.success(f"✅ Interaction retained to Hindsight Cloud under `bank_id='{selected_cid}'`.")
                st.caption(f"Total retained this session: {st.session_state.memories_retained_count}")
            else:
                st.info("⏸️ Retention skipped (Memory toggle OFF or error).")
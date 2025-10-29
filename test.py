# tester_agent.py
import asyncio
from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import (
    ChatMessage, 
    ChatAcknowledgement,
    StartSessionContent,
    TextContent,
    chat_protocol_spec
)
from uagents import Protocol
from datetime import datetime
from uuid import uuid4

# Create test agent
tester = Agent(
    name="tester_agent",
    port=9999,
    endpoint="http://127.0.0.1:9999/submit",
    mailbox=True
)

# Add chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

ORCHESTRATOR_ADDR = "agent1qvwa3w9v2qpe8g87mwcnnsrdq30q7yst077gns8pm9l9ukxrkm8ysvtzgqc"

def mk_chat_message(text: str) -> ChatMessage:
    """Helper to create chat messages"""
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)]
    )

@tester.on_event("startup")
async def on_startup(ctx: Context):
    """Wait a bit, then start the test"""
    print("\n" + "🧪" * 40)
    print("TESTER AGENT STARTED")
    print(f"Agent Address: {ctx.agent.address}")
    print("🧪" * 40 + "\n")
    
    await asyncio.sleep(3)  # Give orchestrator time to be ready
    
    print("📤 Starting chat session with orchestrator...")
    
    # ✅ FIX: Use hyphen instead of underscore
    session_start = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[StartSessionContent(type="start-session")]  # ← FIXED
    )
    
    await ctx.send(ORCHESTRATOR_ADDR, session_start)
    print("✅ Session start message sent\n")
    
    await asyncio.sleep(2)
    
    # Send test procurement request
    test_requests = [
        "I need 10 laptops for video editing under $1500 each",
    ]
    
    for request in test_requests:
        print(f"📤 Sending test request: '{request}'")
        await ctx.send(ORCHESTRATOR_ADDR, mk_chat_message(request))
        print("✅ Request sent\n")
        await asyncio.sleep(1)

@chat_proto.on_message(ChatMessage)
async def on_response(ctx: Context, sender: str, msg: ChatMessage):
    """Handle responses from orchestrator"""
    print("\n" + "=" * 80)
    print("📨 RECEIVED RESPONSE FROM ORCHESTRATOR")
    print(f"Sender: {sender}")
    print(f"Message ID: {msg.msg_id}")
    print("=" * 80)
    
    # Send acknowledgement
    ack = ChatAcknowledgement(
        timestamp=datetime.utcnow(),
        acknowledged_msg_id=msg.msg_id
    )
    await ctx.send(sender, ack)
    
    # Print content
    for idx, item in enumerate(msg.content):
        if isinstance(item, TextContent):
            print(f"\n📝 Response Text:\n{item.text}\n")
    
    print("=" * 80 + "\n")

@chat_proto.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements"""
    print(f"✅ Orchestrator acknowledged message {msg.acknowledged_msg_id}")

# Register protocol
tester.include(chat_proto)

if __name__ == "__main__":
    print("\n🧪 Starting Tester Agent...")
    print("=" * 80)
    print("This agent will:")
    print("  1. Start a chat session with orchestrator")
    print("  2. Send test laptop procurement requests")
    print("  3. Display all responses")
    print("=" * 80 + "\n")
    
    tester.run()
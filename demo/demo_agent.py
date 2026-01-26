"""
Demo Agent with Sentinel Audit Integration

This demonstrates how to instrument a LangChain agent with automatic audit trail capture.
"""
import sys
import os
import time
from datetime import datetime

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk'))

from sentinel_audit import AuditClient, AuditEvent, ActorType, ActionType, EventStatus

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.prompts import PromptTemplate


# Agent configuration
AGENT_INSTANCE_ID = "demo-agent-001"
TRACE_ID = f"trace-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def create_instrumented_tool(tool: Tool, audit_client: AuditClient) -> Tool:
    """
    Wrap a LangChain tool with audit instrumentation
    
    Captures:
    - Tool invocation
    - Input (redacted by default)
    - Output status
    - Latency
    """
    original_func = tool.func
    
    def instrumented_func(*args, **kwargs):
        start_time = time.time()
        
        try:
            # Execute the tool
            result = original_func(*args, **kwargs)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Capture successful execution
            event = AuditEvent(
                agent_instance_id=AGENT_INSTANCE_ID,
                trace_id=TRACE_ID,
                actor=ActorType.AGENT,
                action_type=ActionType.TOOL_CALL,
                resource=tool.name,
                status=EventStatus.SUCCESS,
                latency_ms=latency_ms,
                metadata={
                    "tool_name": tool.name,
                    "tool_description": tool.description,
                    "input": "[REDACTED]",  # Privacy-first
                    "output_length": len(str(result)) if result else 0
                }
            )
            audit_client.capture(event)
            
            return result
        
        except Exception as e:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Capture failed execution
            event = AuditEvent(
                agent_instance_id=AGENT_INSTANCE_ID,
                trace_id=TRACE_ID,
                actor=ActorType.AGENT,
                action_type=ActionType.TOOL_CALL,
                resource=tool.name,
                status=EventStatus.ERROR,
                latency_ms=latency_ms,
                metadata={
                    "tool_name": tool.name,
                    "error": str(e)
                }
            )
            audit_client.capture(event)
            
            raise
    
    # Create new tool with instrumented function
    return Tool(
        name=tool.name,
        description=tool.description,
        func=instrumented_func
    )


def create_demo_agent(audit_client: AuditClient):
    """
    Create a demo LangChain agent with audit instrumentation
    
    Tools:
    - Web search (DuckDuckGo)
    - File read (simulated)
    """
    # Create tools
    search = DuckDuckGoSearchAPIWrapper()
    search_tool = Tool(
        name="web_search",
        description="Search the web for current information. Use this when you need to find recent information or facts.",
        func=search.run
    )
    
    def read_file(filename: str) -> str:
        """Simulated file read tool"""
        # In a real implementation, this would read actual files
        return f"[Simulated file content for: {filename}]"
    
    file_tool = Tool(
        name="read_file",
        description="Read the contents of a file. Input should be a filename.",
        func=read_file
    )
    
    # Instrument tools with audit capture
    instrumented_tools = [
        create_instrumented_tool(search_tool, audit_client),
        create_instrumented_tool(file_tool, audit_client)
    ]
    
    return instrumented_tools


def main():
    """Run the demo agent"""
    print("🚀 Starting Sentinel Audit Demo Agent")
    print(f"📋 Agent Instance ID: {AGENT_INSTANCE_ID}")
    print(f"🔍 Trace ID: {TRACE_ID}")
    print()
    
    # Initialize audit client
    with AuditClient(api_url="http://localhost:8000") as audit_client:
        print("✅ Audit client initialized")
        
        # Create instrumented agent
        tools = create_demo_agent(audit_client)
        print(f"✅ Created agent with {len(tools)} instrumented tools")
        print()
        
        # Simulate agent actions
        print("🤖 Simulating agent actions...")
        print()
        
        # Action 1: Web search
        print("1️⃣  Performing web search...")
        try:
            result = tools[0].func("What is agentic AI?")
            print(f"   ✅ Search completed ({len(result)} chars)")
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
        print()
        
        # Action 2: File read
        print("2️⃣  Reading file...")
        try:
            result = tools[1].func("config.yaml")
            print(f"   ✅ File read completed")
        except Exception as e:
            print(f"   ❌ File read failed: {e}")
        print()
        
        # Flush events
        print("💾 Flushing audit events...")
        audit_client.flush()
        print("   ✅ Events flushed to API")
        print()
        
        print("✨ Demo complete!")
        print()
        print("📊 View audit trail:")
        print(f"   http://localhost:8000/v1/agents/{AGENT_INSTANCE_ID}/events")
        print()
        print("🌐 Open UI:")
        print(f"   Open demo/ui/index.html in your browser")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Test script to reprocess a conversation with the new multi-agent system
and show the improved insights compared to the old system.
"""

import asyncio
import json
from uuid import UUID
from app.services.conversation_intelligence import conversation_intelligence
from app.db.database import get_db_connection

async def test_multi_agent_reprocessing():
    """Reprocess an existing conversation with the new multi-agent system."""
    
    conversation_id = "eb3f7ec1-a229-4369-be99-6f9bf2c4782d"
    
    print("🔄 Testing Multi-Agent Conversation Intelligence System")
    print("="*60)
    
    try:
        # Get conversation data
        async for conn in get_db_connection():
            conversation = await conn.fetchrow("""
                SELECT * FROM ai_conversation_imports WHERE id = $1
            """, UUID(conversation_id))
            
            messages = await conn.fetch("""
                SELECT * FROM ai_conversation_messages 
                WHERE conversation_id = $1 
                ORDER BY sequence_number ASC
            """, UUID(conversation_id))
            
            if not conversation or not messages:
                print("❌ Conversation not found")
                return
            
            print(f"📝 Conversation: {conversation['title']}")
            print(f"💬 Messages: {len(messages)}")
            print(f"🔧 Current version: {conversation.get('agent_processing_version', 'v1.0')}")
            print()
            
            # Test each specialized agent individually
            print("🤖 Testing Specialized Agents:")
            print("-" * 40)
            
            # Convert messages to the format expected by agents
            message_list = [dict(m) for m in messages]
            
            # 1. Technical Content Extractor
            print("🔧 Technical Content Extractor:")
            technical_result = await conversation_intelligence.technical_agent.extract_technical_content(message_list)
            print(f"   - Code snippets found: {len(technical_result.get('code_snippets', []))}")
            print(f"   - Technologies identified: {len(technical_result.get('technologies', []))}")
            print(f"   - Implementation patterns: {len(technical_result.get('implementation_patterns', []))}")
            if technical_result.get('technologies'):
                print(f"   - Key technologies: {[t.get('name', 'Unknown') for t in technical_result['technologies'][:3]]}")
            print()
            
            # 2. Learning Journey Analyzer  
            print("📚 Learning Journey Analyzer:")
            learning_result = await conversation_intelligence.learning_agent.analyze_learning_progression(message_list)
            print(f"   - Learning stages identified: {len(learning_result.get('learning_stages', []))}")
            print(f"   - Breakthrough moments: {len(learning_result.get('breakthrough_moments', []))}")
            if learning_result.get('knowledge_evolution'):
                print(f"   - Evolution summary: {learning_result['knowledge_evolution'][:100]}...")
            print()
            
            # 3. Actionable Insights Extractor
            print("⚡ Actionable Insights Extractor:")
            insights_result = await conversation_intelligence.insights_agent.extract_actionable_insights(message_list)
            print(f"   - Immediate actions: {len(insights_result.get('immediate_actions', []))}")
            print(f"   - Implementation steps: {len(insights_result.get('implementation_steps', []))}")
            print(f"   - Tools & resources: {len(insights_result.get('tools_and_resources', []))}")
            if insights_result.get('immediate_actions'):
                for i, action in enumerate(insights_result['immediate_actions'][:2]):
                    print(f"   - Action {i+1}: {action.get('action', 'N/A')[:80]}...")
            print()
            
            # 4. Knowledge Gap Identifier
            print("🔍 Knowledge Gap Identifier:")
            gaps_result = await conversation_intelligence.gaps_agent.identify_knowledge_gaps(message_list)
            print(f"   - Knowledge gaps found: {len(gaps_result.get('knowledge_gaps', []))}")
            print(f"   - Learning opportunities: {len(gaps_result.get('learning_opportunities', []))}")
            print(f"   - Prerequisites needed: {len(gaps_result.get('prerequisite_knowledge', []))}")
            if gaps_result.get('knowledge_gaps'):
                for i, gap in enumerate(gaps_result['knowledge_gaps'][:2]):
                    print(f"   - Gap {i+1}: {gap.get('gap', 'N/A')[:80]}...")
            print()
            
            print("🎯 COMPARISON WITH OLD SYSTEM:")
            print("-" * 40)
            print("OLD: Random polite messages like 'Thanks for your patience'")
            print("NEW: Specific technical insights, actionable steps, and learning analysis")
            print()
            
            # Reprocess the conversation with the new system
            print("🚀 Reprocessing with Multi-Agent System...")
            result = await conversation_intelligence.process_conversation(UUID(conversation_id))
            
            print("✅ Reprocessing completed!")
            print(f"📊 Processing status: {result.get('processing_status', 'unknown')}")
            
            # Show the difference
            print("\n🔥 NEW INSIGHTS ARE NOW STORED IN DATABASE!")
            print("The frontend should now show much better, actionable insights")
            print("instead of useless polite messages.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multi_agent_reprocessing())
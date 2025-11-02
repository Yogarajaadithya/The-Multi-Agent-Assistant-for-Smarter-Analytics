"""
Test script to directly call LM Studio for hypothesis generation.
This will help diagnose the 0 hypotheses issue.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Initialize LLM exactly as in the multi-agent system
llm = ChatOpenAI(
    model="ibm/granite-3.2-8b",
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
    temperature=0.0,
    timeout=120.0,
    max_retries=2,
)

print("🧪 Testing LM Studio connection...")
print(f"📡 Base URL: {llm.openai_api_base if hasattr(llm, 'openai_api_base') else 'N/A'}")
print(f"🤖 Model: {llm.model_name if hasattr(llm, 'model_name') else llm.model}")
print()

# Simple test prompt
simple_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Respond with a simple JSON object containing a greeting."),
    ("user", "Say hello in JSON format like: {{\"greeting\": \"Hello, world!\"}}")
])

print("🔬 Test 1: Simple JSON generation")
try:
    chain = simple_prompt | llm
    result = chain.invoke({})
    print(f"✅ Success! Response: {result.content}")
except Exception as e:
    print(f"❌ Failed: {e}")
    print(f"Error type: {type(e).__name__}")

print("\n" + "="*70 + "\n")

# Test hypothesis generation with full prompt
hypothesis_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert statistician. Generate ONE hypothesis about employee attrition.\n\n"
     "Return ONLY valid JSON in this exact format:\n"
     "{\n"
     "  \"hypotheses\": [\n"
     "    {\n"
     "      \"hypothesis_id\": 1,\n"
     "      \"null_hypothesis\": \"There is no relationship between department and attrition\",\n"
     "      \"alternative_hypothesis\": \"There is a relationship between department and attrition\",\n"
     "      \"variable_1\": \"department\",\n"
     "      \"variable_2\": \"attrition\",\n"
     "      \"variable_1_type\": \"categorical\",\n"
     "      \"variable_2_type\": \"categorical\",\n"
     "      \"recommended_test\": \"chi-square\",\n"
     "      \"rationale\": \"Different departments may have different attrition rates\"\n"
     "    }\n"
     "  ]\n"
     "}\n\n"
     "Return ONLY the JSON, no other text."),
    ("user", "Generate 1 hypothesis about why employees leave the company.")
])

print("🔬 Test 2: Hypothesis generation")
try:
    chain = hypothesis_prompt | llm
    result = chain.invoke({})
    print(f"✅ Success! Response length: {len(result.content)} characters")
    print(f"📄 First 500 chars: {result.content[:500]}")
    
    # Try to parse as JSON
    import json
    try:
        parsed = json.loads(result.content)
        print(f"✅ Valid JSON with {len(parsed.get('hypotheses', []))} hypotheses")
    except json.JSONDecodeError as je:
        print(f"❌ Invalid JSON: {je}")
        
except TimeoutError as e:
    print(f"❌ TIMEOUT: {e}")
except Exception as e:
    print(f"❌ Failed: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("🏁 Test complete!")

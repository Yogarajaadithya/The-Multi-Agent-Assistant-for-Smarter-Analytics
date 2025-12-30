import asyncio
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_azure_openai():
    try:
        client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        
        print(f"Testing Azure OpenAI connection...")
        print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
        print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
        print(f"API Key: {os.getenv('AZURE_OPENAI_API_KEY')[:10]}...{os.getenv('AZURE_OPENAI_API_KEY')[-4:]}")
        print("\nSending test request...")
        
        response = await client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "user", "content": "Say 'API is working' if you can read this."}
            ],
            max_tokens=50
        )
        
        print("\n✅ SUCCESS! API is working!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: API test failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_azure_openai())

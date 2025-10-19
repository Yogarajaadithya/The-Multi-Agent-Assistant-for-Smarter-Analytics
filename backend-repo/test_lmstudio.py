import asyncio
from openai import AsyncOpenAI
from app.config import get_settings

async def test_lmstudio_connection():
    settings = get_settings()
    client = AsyncOpenAI(
        base_url=settings.lmstudio_base_url,
        api_key=settings.lmstudio_api_key,
    )
    
    try:
        # Test with a simple prompt
        response = await client.chat.completions.create(
            model=settings.lmstudio_model_id,
            messages=[
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=100
        )
        
        print("Connection successful!")
        print("Response:", response.choices[0].message.content)
        
    except Exception as e:
        print("Error connecting to LM Studio:")
        print(e)

if __name__ == "__main__":
    asyncio.run(test_lmstudio_connection())
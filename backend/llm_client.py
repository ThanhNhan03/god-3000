import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

# We can rotate between the two provided API keys or just use the first one
API_KEY = os.getenv("ANTHROPIC_API_KEY_1")

# Initialize the async client
client = AsyncAnthropic(api_key=API_KEY)

async def generate_response(prompt: str, system_prompt: str = ""):
    """Helper function to call Anthropic API."""
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response

async def stream_response(prompt: str, system_prompt: str = ""):
    """Helper function to stream response from Anthropic API."""
    stream = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": prompt}
        ],
        stream=True
    )
    async for event in stream:
        if event.type == "content_block_delta":
            yield event.delta.text

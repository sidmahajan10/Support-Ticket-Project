from pydantic_ai import Agent
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from .models import AgentResponse, TicketDraft
import os
import requests
from typing import List

from dotenv import load_dotenv
load_dotenv()

portkey_client = AsyncOpenAI(
        api_key=os.getenv('PORTKEY_TOKEN'),
        base_url="https://api.portkey.ai/v1"
    )

response_agent = Agent(
    model = OpenAIChatModel(
            model_name="@openrouter-09cb28/google/gemini-2.5-flash-lite",
            provider=OpenAIProvider(openai_client=portkey_client)
        ),
    system_prompt="""You are a helpful support agent. Your goal is to resolve user queries.

IMPORTANT: You must respond with a JSON object containing:
- "category": Either "solution" or "question"
- "content": Your response text

example : 
JSON output : 
{
    'category' : 'question',
    'content' : 'Please detail what errors you see on your console'
}

If you can provide a direct solution, use category "solution" and provide clear, step-by-step instructions.
If you need more information, use category "question" and ask specific, clarifying questions.

Be as detailed and thorough as possible in both the solution or question(s).""",
    output_type=AgentResponse
)

ticket_draft_agent = Agent(
    model = OpenAIChatModel(
            model_name="@openrouter-09cb28/google/gemini-2.5-flash-lite",
            provider=OpenAIProvider(openai_client=portkey_client)
        ),
    system_prompt="""You are a helpful support agent. Your job is to draft a ticket title and description, 
    using the context provided
    IMPORTANT: You must respond with a JSON object containing:
    - "title": The title of the ticket
    - "description": The description of the problem, and the solutions you explored
        example : 
    JSON output : 
    {
        'title' : 'email login issue',
        'description' : 'User not able to login using email. I have suggested trying other 
                        mail ids, but none seem to work.'
    }""",

    
    output_type=TicketDraft
)



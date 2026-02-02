from django.db import models
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class TicketDraft(BaseModel):
    title : str = Field(description = "Suggested ticket title")
    description : str = Field(description = "Suggested description of the ticket")

class AgentResponse(BaseModel):
    category : Literal['solution', 'question'] = Field(description = 'The type of response to return')
    content : str  = Field(default = None, description = 'The solution to the query or clarifying question(s) to the user')

class AgentSession(BaseModel):
    session_id : str
    attempt_count : int = 0
    conversation_history : List[dict] = Field(default = [])
    newAttempt : bool = Field(default = True)


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.crypto import get_random_string
from .models import AgentSession, AgentResponse, TicketDraft
from .agents import response_agent, ticket_draft_agent
import asyncio
import json
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()



agent_sessions = {}
MAX_AGENT_ATTEMPTS = 2


class AgentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='respond')
    def process_query(self, request):

        user_description = request.data.get('description', '')
        session_id = request.data.get('session_id')

        if not session_id : 
            session_id = get_random_string(32)
            session = AgentSession(
                session_id = session_id,
                attempt_count = 0,
                conversation_history = [],
                newAttempt = True
            )

            agent_sessions[session_id] = session

        session = agent_sessions[session_id]
        session.conversation_history.append({'role' : 'user', 'content' : user_description})

        # check if its a new attempt or not
        if(session.newAttempt) : 
            session.attempt_count += 1



        if(session.attempt_count > MAX_AGENT_ATTEMPTS) : 
            # trigger ticket creation agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try :
                prompt = "draft a ticket based on this context" + json.dumps(session.conversation_history)
                result = loop.run_until_complete(ticket_draft_agent.run(prompt))

                logfire.info(f'Here is the output: {result.output=}')

                return Response({
                    'session_id' : session_id,
                    'category' : 'ticket_draft',
                    'content' : result.output.model_dump()
                })
            finally : 
                loop.close()
        else : 
            # trigger response generating agent 
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try : 
                prompt = "solve the user query using this feedback :" + json.dumps(session.conversation_history)
                result = loop.run_until_complete(response_agent.run(prompt))

                session.conversation_history.append({'role' : 'system', 'content' : result.output.content})
                response_category = result.output.category

                logfire.info(f'Here is the output: {result.output=}')

                if(response_category == 'question') :
                    session.newAttempt = False
                    return Response({
                        'session_id' : session_id,
                        'category' : response_category,
                        'content' : result.output.content
                    })
                else : 
                    session.newAttempt = True
                    return Response({
                        'session_id' : session_id,
                        'category' : response_category,
                        'content' : result.output.content
                    })
            finally : 
                loop.close()

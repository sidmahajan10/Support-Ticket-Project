from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Ticket, Comment
from .serializers import TicketSerializer, CommentSerializer
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ViewSet
import os
import requests
import base64
import logging
from dotenv import load_dotenv

# Try to load .env file, but don't fail if it doesn't exist or can't be read
load_dotenv()


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return tickets based on the user's role:
        - Admins (is_staff) see all tickets (including closed ones).
        - Regular users see only their own tickets (any status).
        """
        user = self.request.user

        if user.is_staff:
            queryset = Ticket.objects.all().order_by('-created_at')
        else:
            queryset = Ticket.objects.filter(assignee=user).order_by('-created_at')

        # Filter by status if provided (still applied on top of base queryset)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        """
        Automatically set the assignee to the current user when creating a ticket.
        Also creates a corresponding Jira issue if Jira integration is configured.
        """
        ticket = serializer.save(assignee=self.request.user)

        # Get environment variables
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        jira_project = os.getenv('JIRA_PROJECT')

        # Encode credentials for Basic Auth (correct way)
        credentials = f"{jira_username}:{jira_api_token}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {encoded_credentials}'
        }

        payload = {
            "fields": {
                "project": {
                    "key": jira_project
                },
                "summary": ticket.title,
                "description": ticket.description,
                "issuetype": {
                    "name": "Task"
                }
            }
        }
        
        try:
            response = requests.post(jira_url, json=payload, headers=headers, timeout=10)
            print(response.json())
            
            if response.status_code == 201:
                jira_issue = response.json()
                ticket.jira_issue_key = jira_issue.get('key')
                ticket.jira_issue_id = jira_issue.get('id')
                ticket.save()
                logger.info(
                    f"Successfully created Jira issue {ticket.jira_issue_key} "
                    f"(ID: {ticket.jira_issue_id}) for ticket {ticket.id} (Title: {ticket.title})"
                )
            else:
                logger.error(
                    f"Jira API request failed for ticket {ticket.id}. "
                    f"Status code: {response.status_code}. "
                    f"Response: {response.text}"
                )
        except requests.exceptions.Timeout:
            logger.error(
                f"Jira API request timed out for ticket {ticket.id}. "
                "The request took longer than 10 seconds."
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Jira API connection error for ticket {ticket.id}: {str(e)}. "
                "Check if JIRA_URL is correct and the server is reachable."
            )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Jira API request exception for ticket {ticket.id}: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error creating Jira issue for ticket {ticket.id}: {str(e)}",
                exc_info=True
            )

    # @action(detail=True, methods=['patch'])
    # def update_status(self, request, pk=None):
    #     """
    #     Update ticket status.
        
    #     This endpoint is primarily intended for webhook integration with Jira.
    #     Admins cannot change ticket status from the frontend UI - status changes should come from Jira webhooks.
    #     """
        
    

    

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        ticket_id = self.request.query_params.get('ticket')

        if ticket_id:
            # Filter comments by ticket ID, and ensure the user has access to the ticket
            try:
                if user.is_staff:
                    # Admins can see comments for all tickets (including closed)
                    ticket = Ticket.objects.get(id=ticket_id)
                    return Comment.objects.filter(ticket=ticket).order_by('created_at')
                else:
                    # Regular users can only see comments for their own tickets
                    ticket = Ticket.objects.get(id=ticket_id, assignee=user)
                    return Comment.objects.filter(ticket=ticket).order_by('created_at')
            except Ticket.DoesNotExist:
                return Comment.objects.none()
        else:
            # If no ticket specified, return empty queryset for security
            return Comment.objects.none()
        
    def perform_create(self, serializer):
        user = self.request.user
        ticket = serializer.validated_data['ticket']
        
        # Ensure user has access to the ticket
        if user.is_staff:
            # Admins can comment on all tickets (including closed ones)
            pass
        else:
            # Regular users can only comment on their own tickets
            if ticket.assignee != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You do not have permission to comment on this ticket.')
        
        serializer.save(author=user)



class WebhookViewSet(ViewSet):
    """
    ViewSet for handling webhook integrations.
    All webhook endpoints are accessible without authentication
    but require a valid webhook token.
    """
    permission_classes = [AllowAny]  # Webhooks don't use session auth
    
    # def _validate_webhook_token(self, request):
    #     """
    #     Validate webhook token from headers or request body.
    #     Returns (is_valid, error_response)
    #     """
    #     webhook_token = request.headers.get('X-Webhook-Token') or request.data.get('webhook_token')
    #     expected_token = os.getenv('WEBHOOK_SECRET_TOKEN')
        
    #     if expected_token and webhook_token != expected_token:
    #         return False, Response(
    #             {'error': 'Invalid webhook token'},
    #             status=status.HTTP_401_UNAUTHORIZED
    #         )
        
    #     return True, None
    
    @action(detail=False, methods=['post'], url_path='jira/update_status')
    def jira_update_status(self, request):
        """
        Webhook endpoint to update ticket status from Jira webhook.
        
        URL: /api/webhooks/jira/update_status/
        Jira sends POST requests with issue data in the payload.
        """
        # Validate webhook token
        # is_valid, error_response = self._validate_webhook_token(request)
        # if not is_valid:
        #     return error_response
        
        # Extract issue data from Jira webhook payload
        issue = request.data.get('issue', {})
        if not issue:
            return Response(
                {'error': 'Missing issue data in webhook payload'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        jira_issue_id = issue.get('id')
        jira_issue_key = issue.get('key')
        jira_status = issue.get('fields', {}).get('status', {}).get('name', '').lower()
        
        if not jira_issue_id:
            return Response(
                {'error': 'Missing Jira issue ID in webhook payload'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Map Jira status names to your status values
        status_mapping = {
            'open': 'open',
            'in progress': 'in_progress',
            'in_progress': 'in_progress',
            'closed': 'closed',
        }
        
        new_status = status_mapping.get(jira_status)
        if not new_status:
            logger.warning(
                f"Unknown Jira status '{jira_status}' for issue {jira_issue_key} (ID: {jira_issue_id}). "
                f"Available statuses: {list(status_mapping.keys())}"
            )
            return Response(
                {'error': f'Unknown Jira status: {jira_status}. Supported statuses: {list(status_mapping.keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find ticket by jira_issue_id (stored as string)
        try:
            ticket = Ticket.objects.get(jira_issue_id=str(jira_issue_id))
        except Ticket.DoesNotExist:
            logger.warning(
                f"Ticket not found for Jira issue {jira_issue_key} (ID: {jira_issue_id})"
            )
            return Response(
                {'error': f'Ticket with Jira issue ID {jira_issue_id} (key: {jira_issue_key}) not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only update if status actually changed
        if ticket.status == new_status:
            logger.info(
                f"Ticket {ticket.id} status unchanged ({new_status}) "
                f"for Jira issue {jira_issue_key} (ID: {jira_issue_id})"
            )
        else:
            old_status = ticket.status
            ticket.status = new_status
            ticket.save()
            
            logger.info(
                f"Ticket {ticket.id} status updated from '{old_status}' to '{new_status}' "
                f"via Jira webhook (Jira issue: {jira_issue_key}, ID: {jira_issue_id})"
            )
        
        serializer = TicketSerializer(ticket)
        return Response({
            'message': 'Ticket status updated successfully',
            'ticket': serializer.data,
            'jira_issue_key': jira_issue_key,
            'jira_issue_id': jira_issue_id,
            'status_mapped_from': jira_status,
            'status_mapped_to': new_status
        }, status=status.HTTP_200_OK)
    
    # Example: Add more webhook endpoints here as needed
    # @action(detail=False, methods=['post'], url_path='slack/notify')
    # def slack_notify(self, request):
    #     """Slack webhook endpoint"""
    #     pass


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Ticket, Comment
from .serializers import TicketSerializer, CommentSerializer
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ViewSet
import json
import os
import requests
from requests.auth import HTTPBasicAuth
import base64
import logging
from dotenv import load_dotenv
from django.contrib.auth import get_user_model
User = get_user_model()



# Try to load .env file, but don't fail if it doesn't exist or can't be read
try:
    load_dotenv()
except Exception as e:
    logging.getLogger(__name__).warning(f"Could not load .env file: {e}")

logger = logging.getLogger(__name__)


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None # Disable pagination for the ticket list as filtering is done at the frontend

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
        
        # Prevent admins from commenting - they can only view comments
        if user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Admins cannot comment on tickets. They can only view comments.')
        
        # Regular users can only comment on their own tickets
        if ticket.assignee != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have permission to comment on this ticket.')
        
        comment = serializer.save(author=user)

        # Only create Jira comment if ticket has a Jira issue ID
        if not ticket.jira_issue_id:
            logger.warning(
                f"Ticket {ticket.id} does not have a Jira issue ID. Skipping Jira comment creation."
            )
            return

        jira_base_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')

        jira_base_url = jira_base_url.rstrip('/')
        jira_comment_url = f"{jira_base_url}/{ticket.jira_issue_id}/comment"

        auth = HTTPBasicAuth(jira_username, jira_api_token)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = {
            "body": comment.content
        }

        try:
            response = requests.post(
                jira_comment_url,
                json=payload,
                headers=headers,
                auth=auth,
                timeout=10
            )

            if response.status_code == 201:
                jira_comment = response.json()
                comment.jira_comment_id = jira_comment.get('id')
                comment.save()
                logger.info(
                    f"Successfully created Jira comment {comment.jira_comment_id} "
                    f"for ticket {comment.ticket.id} (Title: {comment.ticket.title})"
                )
            else:
                logger.error(
                    f"Jira API request failed for comment {comment.id}. "
                    f"Status code: {response.status_code}. "
                    f"Response: {response.text}"
                )
        except requests.exceptions.Timeout:
            logger.error(
                f"Jira API request timed out for comment {comment.id}. "
                "The request took longer than 10 seconds."
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Jira API connection error for comment {comment.id}: {str(e)}. "
                "Check if JIRA_URL is correct and the server is reachable."
            )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Jira API request exception for comment {comment.id}: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error creating Jira comment for comment {comment.id}: {str(e)}",
                exc_info=True
            )
        



class WebhookViewSet(ViewSet):
    """
    ViewSet for handling webhook integrations.
    All webhook endpoints are accessible without authentication
    but require a valid webhook token.
    """
    permission_classes = [AllowAny]  # Webhooks don't use session auth
    
    
    @action(detail=False, methods=['post'], url_path='jira/update_status')
    def jira_update_status(self, request):
        """
        Webhook endpoint to update ticket status from Jira webhook.
        
        URL: /api/webhooks/jira/update_status/
        Jira sends POST requests with issue data in the payload.
        """
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
    
   
    @action(detail=False, methods=['post'], url_path='jira/comment_created')
    def jira_comment_created(self, request):
        """
        Webhook endpoint to create a comment from Jira webhook.
        
        URL: /api/webhooks/jira/comment_created/
        Jira sends POST requests when a comment is created on an issue.
        """
        # Extract issue and comment data from Jira webhook payload
        issue = request.data.get('issue', {})
        comment = request.data.get('comment', {})
        
        if not issue:
            return Response(
                {'error': 'Missing issue data in webhook payload'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not comment:
            return Response(
                {'error': 'Missing comment data in webhook payload'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        jira_issue_id = issue.get('id')
        jira_issue_key = issue.get('key')
        jira_comment_id = comment.get('id')
        comment_body = comment.get('body', '')
        comment_author = comment.get('author', {})
        comment_created = comment.get('created', '')
        
        if not jira_issue_id:
            return Response(
                {'error': 'Missing Jira issue ID in webhook payload'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find ticket by jira_issue_id
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
        
        # Check if comment already exists (prevent duplicates)
        if jira_comment_id and Comment.objects.filter(jira_comment_id=str(jira_comment_id)).exists():
            logger.info(
                f"Comment with Jira ID {jira_comment_id} already exists. Skipping creation."
            )
            existing_comment = Comment.objects.get(jira_comment_id=str(jira_comment_id))
            serializer = CommentSerializer(existing_comment)
            return Response({
                'message': 'Comment already exists',
                'comment': serializer.data
            }, status=status.HTTP_200_OK)
        
        
        # Get the first admin user (staff user)
        admin_user = User.objects.filter(is_staff=True).first()
        
        if not admin_user:
            # Fallback: if no admin exists, use ticket assignee
            logger.warning(
                f"No admin user found. Using ticket assignee {ticket.assignee.username} as comment author."
            )
            comment_author_user = ticket.assignee
        else:
            comment_author_user = admin_user
            logger.info(
                f"Using admin user {admin_user.username} as comment author for Jira webhook comment."
            )
        
        # Extract text from comment body (Jira may send HTML or ADF format)
        # If Jira sends HTML, you might need to strip tags
        import re
        if isinstance(comment_body, str):
            # Remove HTML tags if present
            comment_content = re.sub(r'<[^>]+>', '', comment_body)
        elif isinstance(comment_body, dict):
            # If Jira sends ADF (Atlassian Document Format), extract text
            # This is a simplified version - you may need more complex parsing
            comment_content = str(comment_body)
        else:
            comment_content = str(comment_body) if comment_body else ''
        
        # Create the comment
        try:
            new_comment = Comment.objects.create(
                ticket=ticket,
                author=comment_author_user,
                content=comment_content,
                jira_comment_id=str(jira_comment_id) if jira_comment_id else None
            )
            
            logger.info(
                f"Successfully created comment {new_comment.id} from Jira webhook "
                f"(Jira comment ID: {jira_comment_id}, Issue: {jira_issue_key})"
            )
            
            serializer = CommentSerializer(new_comment)
            return Response({
                'message': 'Comment created successfully from Jira webhook',
                'comment': serializer.data,
                'jira_issue_key': jira_issue_key,
                'jira_comment_id': jira_comment_id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(
                f"Error creating comment from Jira webhook: {str(e)}",
                exc_info=True
            )
            return Response(
                {'error': f'Failed to create comment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


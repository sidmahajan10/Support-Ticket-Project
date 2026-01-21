from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Ticket, Comment
from .serializers import TicketSerializer, CommentSerializer


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
        """
        serializer.save(assignee=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update ticket status.
        """
        new_status = request.data.get('status')

        if new_status not in ['open', 'in_progress', 'closed']:
            return Response(
                {'error': 'Invalid status. Must be one of: open, in_progress, closed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce role-based rules:
        # - Admins (is_staff) can set any status.
        # - Regular users CANNOT change ticket status at all after creation.
        user = request.user
        if not user.is_staff:
            return Response(
                {'error': 'Only admins can change ticket status.'},
                status=status.HTTP_403_FORBIDDEN
            )

        ticket = self.get_object()
        ticket.status = new_status
        ticket.save()
        
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)
    

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



        
        



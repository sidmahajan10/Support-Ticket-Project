from rest_framework import serializers
from .models import Ticket, Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source='assignee.name', read_only=True)
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'title', 'description', 'status', 'created_at', 'updated_at', 
                  'assignee', 'assignee_name', 'assignee_username']
        read_only_fields = ['assignee', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'ticket', 'author', 'author_name', 'author_username', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

from django.db import models
from django.conf import settings

# Create your models here.

class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ], default='open')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    jira_issue_key = models.CharField(max_length=50, blank=True, null=True, help_text='Jira issue key if synced to Jira')
    jira_issue_id = models.CharField(max_length=50, blank=True, null=True, help_text='Jira issue ID if synced to Jira')

    def __str__(self):
        return self.title


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.PROTECT
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    jira_comment_id = models.CharField(max_length=50, blank=True, null=True, help_text='Jira comment ID if synced to Jira')

    def __str__(self):
        return self.content
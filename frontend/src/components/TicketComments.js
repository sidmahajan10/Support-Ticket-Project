import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './TicketComments.css';

const TicketComments = ({ ticket, onClose }) => {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const commentsEndRef = useRef(null);

  useEffect(() => {
    fetchComments();
    // Auto-refresh comments every 5 seconds
    const interval = setInterval(fetchComments, 5000);
    return () => clearInterval(interval);
  }, [ticket.id]);

  useEffect(() => {
    scrollToBottom();
  }, [comments]);

  const scrollToBottom = () => {
    commentsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchComments = async () => {
    try {
      const response = await axios.get('/api/comments/', {
        params: { ticket: ticket.id },
        withCredentials: true,
      });
      setComments(response.data.results || response.data);
      setError('');
    } catch (err) {
      console.error('Error fetching comments:', err);
      if (err.response?.status !== 404) {
        setError('Failed to load comments. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setSubmitting(true);
    setError('');

    try {
      await axios.post(
        '/api/comments/',
        {
          ticket: ticket.id,
          content: newComment.trim(),
        },
        { withCredentials: true }
      );
      setNewComment('');
      fetchComments();
    } catch (err) {
      setError('Failed to post comment. Please try again.');
      console.error('Error posting comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isMyComment = (comment) => {
    return comment.author === user?.id || comment.author_username === user?.username;
  };

  if (loading) {
    return (
      <div className="comments-modal">
        <div className="comments-container">
          <div className="comments-header">
            <h3>{ticket.title}</h3>
            <button onClick={onClose} className="close-btn">×</button>
          </div>
          <div className="loading">Loading comments...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="comments-modal" onClick={(e) => e.target.classList.contains('comments-modal') && onClose()}>
      <div className="comments-container">
        <div className="comments-header">
          <div>
            <h3>{ticket.title}</h3>
            <p className="ticket-status">Status: <span className={`status-${ticket.status}`}>{ticket.status.replace('_', ' ').toUpperCase()}</span></p>
          </div>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <div className="comments-list">
          {comments.length === 0 ? (
            <div className="no-comments">
              <p>No comments yet. Be the first to comment!</p>
            </div>
          ) : (
            comments.map((comment) => (
              <div
                key={comment.id}
                className={`comment-item ${isMyComment(comment) ? 'my-comment' : ''}`}
              >
                <div className="comment-header">
                  <span className="comment-author">
                    {comment.author_name || comment.author_username}
                    {isMyComment(comment) && <span className="you-badge">You</span>}
                  </span>
                  <span className="comment-time">{formatDate(comment.created_at)}</span>
                </div>
                <div className="comment-content">{comment.content}</div>
              </div>
            ))
          )}
          <div ref={commentsEndRef} />
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="comment-form">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Type your comment..."
            rows="3"
            disabled={submitting}
          />
          <button type="submit" className="btn btn-primary" disabled={submitting || !newComment.trim()}>
            {submitting ? 'Posting...' : 'Post Comment'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TicketComments;

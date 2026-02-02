import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './AgentTicketFlow.css';

const AgentTicketFlow = ({ onTicketCreated, onCancel }) => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [ticketDraft, setTicketDraft] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastRequest, setLastRequest] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when component mounts or after sending
  useEffect(() => {
    if (!loading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [loading, messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendToAgent = async (text, sessionIdParam = null) => {
    console.log('sendToAgent called with:', { text, sessionIdParam });
    setLoading(true);
    setError('');
    
    // Store request for potential retry
    setLastRequest({ text, sessionIdParam });
    
    // Add user message to chat
    const userMessage = { role: 'user', content: text, type: 'message' };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    
    try {
      const payload = {
        description: text
      };
      
      if (sessionIdParam) {
        payload.session_id = sessionIdParam;
      }

      console.log('Sending POST request to /api/agents/respond/ with payload:', payload);
      
      const response = await axios.post(
        '/api/agents/respond/',
        payload,
        { 
          withCredentials: true,
          timeout: 60000,
        }
      );
      
      console.log('Response received:', response.data);

      const data = response.data;
      
      // Store session ID
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // Handle different response categories
      if (data.category === 'ticket_draft') {
        // Ticket draft received
        let draftContent = data.content;
        if (typeof draftContent === 'string') {
          try {
            draftContent = JSON.parse(draftContent);
          } catch (e) {
            console.error('Error parsing ticket draft:', e);
            draftContent = { title: '', description: draftContent };
          }
        }
        setTicketDraft({
          title: draftContent.title || '',
          description: draftContent.description || ''
        });
        
        // Add assistant message about ticket draft
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'I couldn\'t resolve this after multiple attempts. I\'ve drafted a ticket for you to review and submit.',
          type: 'ticket_draft',
          draft: draftContent
        }]);
      } else if (data.category === 'solution') {
        // Solution provided
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.content,
          type: 'solution'
        }]);
      } else if (data.category === 'question') {
        // Question asked
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.content,
          type: 'question'
        }]);
      }
    } catch (err) {
      console.error('Agent API error:', err);
      console.error('Error details:', {
        message: err.message,
        code: err.code,
        response: err.response,
        request: err.request,
        config: err.config
      });
      
      // Add error message to chat
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Sorry, I encountered an error. Please try again.',
        type: 'error'
      }]);
      
      // Handle different types of errors
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('The request took too long. The AI agent may be processing. Please try again in a moment.');
      } else if (err.code === 'ECONNRESET' || err.code === 'ERR_NETWORK' || !err.response) {
        setError('Connection to server was lost. Please check if the backend server is running and try again.');
      } else if (err.response) {
        const errorMsg = err.response.data?.error || 
                        err.response.data?.detail || 
                        `Server error: ${err.response.status} ${err.response.statusText}`;
        setError(errorMsg);
      } else {
        setError('Failed to communicate with the AI agent. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    
    await sendToAgent(inputText.trim(), sessionId);
  };

  const handleAcceptSolution = () => {
    // User accepted solution - close the flow
    if (onTicketCreated) {
      onTicketCreated();
    }
  };

  const handleRejectSolution = async () => {
    // User rejected solution - continue with agent
    await sendToAgent('The previous solution did not work. Please try again.', sessionId);
  };

  const handleTicketDraftSubmit = async (e) => {
    e.preventDefault();
    if (!ticketDraft.title.trim() || !ticketDraft.description.trim()) {
      setError('Please fill in both title and description');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await axios.post(
        '/api/tickets/',
        {
          title: ticketDraft.title,
          description: ticketDraft.description
        },
        { withCredentials: true }
      );
      
      if (onTicketCreated) {
        onTicketCreated();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create ticket. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditDraft = (field, value) => {
    setTicketDraft(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="agent-chat-container">
      <div className="chat-header">
        <div className="chat-header-content">
          <h3>AI Support Assistant</h3>
          <button onClick={onCancel} className="close-btn" title="Close">×</button>
        </div>
      </div>

      <div className="chat-messages" id="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-icon">🤖</div>
            <h4>How can I help you today?</h4>
            <p>Describe your issue or question, and I'll assist you. If I can't resolve it, I'll help you create a support ticket.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            {msg.role === 'user' && (
              <div className="message user-message">
                <div className="message-avatar user-avatar">You</div>
                <div className="message-bubble user-bubble">
                  <div className="message-text">{msg.content}</div>
                </div>
              </div>
            )}

            {msg.role === 'assistant' && (
              <div className="message assistant-message">
                <div className="message-avatar assistant-avatar">AI</div>
                <div className="message-bubble assistant-bubble">
                  {msg.type === 'solution' && (
                    <>
                      <div className="message-text">{msg.content}</div>
                      <div className="message-actions">
                        <button
                          onClick={handleAcceptSolution}
                          className="action-btn accept-btn"
                          disabled={loading}
                        >
                          ✓ This Solved My Issue
                        </button>
                        <button
                          onClick={handleRejectSolution}
                          className="action-btn reject-btn"
                          disabled={loading}
                        >
                          ✗ This Didn't Work
                        </button>
                      </div>
                    </>
                  )}
                  
                  {msg.type === 'question' && (
                    <div className="message-text">{msg.content}</div>
                  )}

                  {msg.type === 'ticket_draft' && (
                    <div className="ticket-draft-message">
                      <div className="message-text">{msg.content}</div>
                      {ticketDraft && (
                        <div className="draft-form">
                          <div className="draft-field">
                            <label>Title</label>
                            <input
                              type="text"
                              value={ticketDraft.title}
                              onChange={(e) => handleEditDraft('title', e.target.value)}
                              placeholder="Ticket title"
                              disabled={loading}
                            />
                          </div>
                          <div className="draft-field">
                            <label>Description</label>
                            <textarea
                              value={ticketDraft.description}
                              onChange={(e) => handleEditDraft('description', e.target.value)}
                              placeholder="Ticket description"
                              rows="4"
                              disabled={loading}
                            />
                          </div>
                          <button
                            onClick={handleTicketDraftSubmit}
                            className="action-btn submit-btn"
                            disabled={loading || !ticketDraft.title.trim() || !ticketDraft.description.trim()}
                          >
                            {loading ? 'Creating...' : 'Create Ticket'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {msg.role === 'system' && (
              <div className="message system-message">
                <div className="message-text error-text">{msg.content}</div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message-wrapper assistant">
            <div className="message assistant-message">
              <div className="message-avatar assistant-avatar">AI</div>
              <div className="message-bubble assistant-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          {lastRequest && (
            <button
              onClick={() => {
                setError('');
                sendToAgent(lastRequest.text, lastRequest.sessionIdParam);
              }}
              className="retry-btn"
              disabled={loading}
            >
              Retry
            </button>
          )}
        </div>
      )}

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
            rows="1"
            disabled={loading}
            className="chat-input"
          />
          <button
            type="submit"
            className="send-button"
            disabled={loading || !inputText.trim()}
            title="Send message"
          >
            {loading ? (
              <div className="send-spinner"></div>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AgentTicketFlow;

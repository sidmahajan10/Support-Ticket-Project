import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TicketComments from './TicketComments';
import './TicketList.css';

const TicketList = ({ isAdmin = false }) => {
  const [tickets, setTickets] = useState([]);
  const [filteredTickets, setFilteredTickets] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTicket, setSelectedTicket] = useState(null);

  useEffect(() => {
    fetchTickets();
  }, []);

  useEffect(() => {
    if (statusFilter === 'all') {
      setFilteredTickets(tickets);
    } else {
      setFilteredTickets(tickets.filter((ticket) => ticket.status === statusFilter));
    }
  }, [statusFilter, tickets]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/tickets/', {
        withCredentials: true,
      });
      setTickets(response.data.results || response.data);
      setError('');
    } catch (err) {
      setError('Failed to load tickets. Please try again.');
      console.error('Error fetching tickets:', err);
    } finally {
      setLoading(false);
    }
  };


  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'open':
        return 'status-badge status-open';
      case 'in_progress':
        return 'status-badge status-in-progress';
      case 'closed':
        return 'status-badge status-closed';
      default:
        return 'status-badge';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return <div className="loading">Loading tickets...</div>;
  }

  return (
    <div className="ticket-list-container">
      <div className="filter-section">
        <label htmlFor="status-filter">Filter by Status:</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="status-filter"
        >
          <option value="all">All Tickets</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
        <span className="ticket-count">
          {filteredTickets.length} ticket{filteredTickets.length !== 1 ? 's' : ''}
        </span>
      </div>

      {error && <div className="error-message">{error}</div>}

      {filteredTickets.length === 0 ? (
        <div className="empty-state">
          <p>No tickets found.</p>
          {statusFilter !== 'all' && (
            <p className="empty-state-hint">
              Try changing the filter or create a new ticket.
            </p>
          )}
        </div>
      ) : (
        <div className="tickets-grid">
          {filteredTickets.map((ticket) => (
            <div 
              key={ticket.id} 
              className="ticket-card clickable"
              onClick={() => setSelectedTicket(ticket)}
            >
              <div className="ticket-header">
                <h3 className="ticket-title">{ticket.title}</h3>
                <span className={getStatusBadgeClass(ticket.status)}>
                  {ticket.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <p className="ticket-description">{ticket.description}</p>

              <div className="ticket-footer">
                <div className="ticket-meta">
                  <span className="ticket-date">
                    Created: {formatDate(ticket.created_at)}
                  </span>
                  {ticket.updated_at !== ticket.created_at && (
                    <span className="ticket-date">
                      Updated: {formatDate(ticket.updated_at)}
                    </span>
                  )}
                </div>

              </div>
            </div>
          ))}
        </div>
      )}

      {selectedTicket && (
        <TicketComments
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
        />
      )}
    </div>
  );
};

export default TicketList;

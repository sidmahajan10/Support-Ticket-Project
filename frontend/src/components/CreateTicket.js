import React, { useState } from 'react';
import axios from 'axios';
import './CreateTicket.css';

const CreateTicket = ({ onTicketCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await axios.post(
        '/api/tickets/',
        formData,
        { withCredentials: true }
      );
      setSuccess('Ticket created successfully!');
      setFormData({ title: '', description: '' });
      setTimeout(() => {
        onTicketCreated();
      }, 1500);
    } catch (err) {
      setError(
        err.response?.data?.error || 'Failed to create ticket. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card create-ticket-card">
      <h3>Create New Ticket</h3>
      <form onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Enter ticket title"
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            placeholder="Describe your issue or request..."
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Creating...' : 'Create Ticket'}
        </button>
      </form>
    </div>
  );
};

export default CreateTicket;

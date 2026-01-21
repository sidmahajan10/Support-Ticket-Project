import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import TicketList from './TicketList';
import CreateTicket from './CreateTicket';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const isAdmin = user?.is_staff || false;
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  const handleTicketCreated = () => {
    setShowCreateForm(false);
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-title">Support Ticket System</h1>
          <div className="navbar-user">
            <span className="user-name">Welcome, {user?.name || user?.username}</span>
            <button onClick={handleLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="dashboard-content">
        <div className="dashboard-header">
          <div>
            <h2>{isAdmin ? 'All Tickets' : 'My Tickets'}</h2>
            {isAdmin && (
              <p style={{ marginTop: '4px', color: '#666', fontSize: '14px' }}>
                Admin view: showing all tickets including closed ones.
              </p>
            )}
          </div>
          {!isAdmin && (
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="btn btn-primary"
            >
              {showCreateForm ? 'Cancel' : '+ Create New Ticket'}
            </button>
          )}
        </div>

        {showCreateForm && (
          <div className="create-ticket-section">
            <CreateTicket onTicketCreated={handleTicketCreated} />
          </div>
        )}

        <TicketList key={refreshKey} isAdmin={isAdmin} />
      </div>
    </div>
  );
};

export default Dashboard;

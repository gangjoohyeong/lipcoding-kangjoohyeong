import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { matchRequestAPI, userAPI } from '../services/api';
import { MatchRequest, User } from '../types';
import './Requests.css';

const Requests: React.FC = () => {
  const { user } = useAuth();
  const [incomingRequests, setIncomingRequests] = useState<MatchRequest[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<MatchRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<{[key: number]: boolean}>({});
  const [userProfiles, setUserProfiles] = useState<{[key: number]: User}>({});

  useEffect(() => {
    fetchRequests();
  }, [user]);

  const fetchRequests = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError('');

      if (user.role === 'mentor') {
        const incoming = await matchRequestAPI.getIncoming();
        setIncomingRequests(incoming);
        
        // 멘티 정보 가져오기
        const menteeIds = Array.from(new Set(incoming.map((req: MatchRequest) => req.menteeId))) as number[];
        const profiles: {[key: number]: User} = {};
        
        for (const menteeId of menteeIds) {
          try {
            // 실제로는 사용자 ID로 프로필을 가져오는 API가 필요하지만,
            // 현재는 현재 사용자 정보만 가져올 수 있으므로 기본값 사용
            profiles[menteeId] = {
              id: menteeId,
              email: `mentee${menteeId}@example.com`,
              role: 'mentee',
              profile: {
                name: `Mentee ${menteeId}`,
                bio: 'Mentee profile',
                imageUrl: 'https://placehold.co/500x500.jpg?text=MENTEE'
              }
            };
          } catch (err) {
            // 프로필을 가져올 수 없는 경우 기본값 사용
          }
        }
        setUserProfiles(profiles);
      } else {
        const outgoing = await matchRequestAPI.getOutgoing();
        setOutgoingRequests(outgoing);
        
        // 멘토 정보 가져오기
        const mentorIds = Array.from(new Set(outgoing.map((req: any) => req.mentorId))) as number[];
        const profiles: {[key: number]: User} = {};
        
        for (const mentorId of mentorIds) {
          try {
            profiles[mentorId] = {
              id: mentorId,
              email: `mentor${mentorId}@example.com`,
              role: 'mentor',
              profile: {
                name: `Mentor ${mentorId}`,
                bio: 'Mentor profile',
                imageUrl: 'https://placehold.co/500x500.jpg?text=MENTOR',
                skills: ['React', 'Node.js']
              }
            };
          } catch (err) {
            // 프로필을 가져올 수 없는 경우 기본값 사용
          }
        }
        setUserProfiles(profiles);
      }
    } catch (err: any) {
      setError('Failed to fetch requests');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (requestId: number) => {
    try {
      setActionLoading(prev => ({ ...prev, [requestId]: true }));
      await matchRequestAPI.accept(requestId);
      
      // 요청 목록 새로고침
      await fetchRequests();
      alert('Request accepted successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to accept request');
    } finally {
      setActionLoading(prev => ({ ...prev, [requestId]: false }));
    }
  };

  const handleReject = async (requestId: number) => {
    try {
      setActionLoading(prev => ({ ...prev, [requestId]: true }));
      await matchRequestAPI.reject(requestId);
      
      // 요청 목록 새로고침
      await fetchRequests();
      alert('Request rejected');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject request');
    } finally {
      setActionLoading(prev => ({ ...prev, [requestId]: false }));
    }
  };

  const handleCancel = async (requestId: number) => {
    try {
      setActionLoading(prev => ({ ...prev, [requestId]: true }));
      await matchRequestAPI.cancel(requestId);
      
      // 요청 목록 새로고침
      await fetchRequests();
      alert('Request cancelled');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel request');
    } finally {
      setActionLoading(prev => ({ ...prev, [requestId]: false }));
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending': return 'status-pending';
      case 'accepted': return 'status-accepted';
      case 'rejected': return 'status-rejected';
      case 'cancelled': return 'status-cancelled';
      default: return '';
    }
  };

  if (!user) return null;

  return (
    <div className="page-container">
      <div className="requests-container">
        <div className="requests-header">
          <h1>
            {user.role === 'mentor' ? 'Incoming Requests' : 'My Requests'}
          </h1>
          <p>
            {user.role === 'mentor' 
              ? 'Manage mentoring requests from mentees'
              : 'Track your mentoring requests'}
          </p>
        </div>

        {loading ? (
          <div className="loading">Loading requests...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <div className="requests-list">
            {user.role === 'mentor' ? (
              // 멘토용: 받은 요청들
              incomingRequests.length === 0 ? (
                <div className="no-requests">No incoming requests</div>
              ) : (
                incomingRequests.map((request) => (
                  <div key={request.id} className="request-card">
                    <div className="request-header">
                      <div className="user-info">
                        <img
                          src={userProfiles[request.menteeId]?.profile.imageUrl || 'https://placehold.co/500x500.jpg?text=MENTEE'}
                          alt="Mentee"
                          className="user-avatar"
                        />
                        <div>
                          <h3>{userProfiles[request.menteeId]?.profile.name || `Mentee ${request.menteeId}`}</h3>
                          <p>{userProfiles[request.menteeId]?.email || `mentee${request.menteeId}@example.com`}</p>
                        </div>
                      </div>
                      <span className={`status-badge ${getStatusBadgeClass(request.status)}`}>
                        {request.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="request-message" data-mentee={request.menteeId.toString()}>
                      <h4>Message:</h4>
                      <p>{request.message}</p>
                    </div>

                    {request.status === 'pending' && (
                      <div className="request-actions">
                        <button
                          id="accept"
                          onClick={() => handleAccept(request.id)}
                          disabled={actionLoading[request.id]}
                          className="accept-button"
                        >
                          {actionLoading[request.id] ? 'Processing...' : 'Accept'}
                        </button>
                        <button
                          id="reject"
                          onClick={() => handleReject(request.id)}
                          disabled={actionLoading[request.id]}
                          className="reject-button"
                        >
                          {actionLoading[request.id] ? 'Processing...' : 'Reject'}
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )
            ) : (
              // 멘티용: 보낸 요청들
              outgoingRequests.length === 0 ? (
                <div className="no-requests">No outgoing requests</div>
              ) : (
                outgoingRequests.map((request: any) => (
                  <div key={request.id} className="request-card">
                    <div className="request-header">
                      <div className="user-info">
                        <img
                          src={userProfiles[request.mentorId]?.profile.imageUrl || 'https://placehold.co/500x500.jpg?text=MENTOR'}
                          alt="Mentor"
                          className="user-avatar"
                        />
                        <div>
                          <h3>{userProfiles[request.mentorId]?.profile.name || `Mentor ${request.mentorId}`}</h3>
                          <p>{userProfiles[request.mentorId]?.email || `mentor${request.mentorId}@example.com`}</p>
                        </div>
                      </div>
                      <span id="request-status" className={`status-badge ${getStatusBadgeClass(request.status)}`}>
                        {request.status.toUpperCase()}
                      </span>
                    </div>

                    {request.status === 'pending' && (
                      <div className="request-actions">
                        <button
                          id="cancel"
                          onClick={() => handleCancel(request.id)}
                          disabled={actionLoading[request.id]}
                          className="cancel-button"
                        >
                          {actionLoading[request.id] ? 'Cancelling...' : 'Cancel Request'}
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Requests;
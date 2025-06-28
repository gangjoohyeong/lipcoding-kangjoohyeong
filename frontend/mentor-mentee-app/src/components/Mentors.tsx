import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { mentorAPI, matchRequestAPI } from '../services/api';
import { MentorListItem } from '../types';
import './Mentors.css';

const Mentors: React.FC = () => {
  const { user } = useAuth();
  const [mentors, setMentors] = useState<MentorListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchSkill, setSearchSkill] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [requestMessages, setRequestMessages] = useState<{[key: number]: string}>({});
  const [sendingRequest, setSendingRequest] = useState<{[key: number]: boolean}>({});

  useEffect(() => {
    fetchMentors();
  }, [searchSkill, sortBy]);

  const fetchMentors = async () => {
    try {
      setLoading(true);
      const data = await mentorAPI.getMentors(searchSkill || undefined, sortBy || undefined);
      setMentors(data);
    } catch (err: any) {
      setError('Failed to fetch mentors');
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (mentorId: number) => {
    if (!user || !requestMessages[mentorId]?.trim()) {
      return;
    }

    try {
      setSendingRequest(prev => ({ ...prev, [mentorId]: true }));
      await matchRequestAPI.create({
        mentorId,
        menteeId: user.id,
        message: requestMessages[mentorId],
      });
      
      // 요청 성공 후 메시지 초기화
      setRequestMessages(prev => ({ ...prev, [mentorId]: '' }));
      alert('Request sent successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to send request');
    } finally {
      setSendingRequest(prev => ({ ...prev, [mentorId]: false }));
    }
  };

  // 멘티가 아니면 접근 불가
  if (user?.role !== 'mentee') {
    return (
      <div className="page-container">
        <div className="error-message">Only mentees can access the mentor list</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="mentors-container">
        <div className="mentors-header">
          <h1>Find Your Mentor</h1>
          <p>Browse through our amazing mentors and find the perfect match</p>
        </div>

        <div className="mentors-filters">
          <div className="filter-group">
            <label htmlFor="search">Search by Skill</label>
            <input
              type="text"
              id="search"
              value={searchSkill}
              onChange={(e) => setSearchSkill(e.target.value)}
              placeholder="e.g., React, Python, Node.js..."
            />
          </div>

          <div className="filter-group">
            <label>Sort by</label>
            <div className="sort-options">
              <label>
                <input
                  type="radio"
                  id="name"
                  name="sort"
                  value="name"
                  checked={sortBy === 'name'}
                  onChange={(e) => setSortBy(e.target.value)}
                />
                Name
              </label>
              <label>
                <input
                  type="radio"
                  id="skill"
                  name="sort"
                  value="skill"
                  checked={sortBy === 'skill'}
                  onChange={(e) => setSortBy(e.target.value)}
                />
                Skills
              </label>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading mentors...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <div className="mentors-list">
            {mentors.length === 0 ? (
              <div className="no-mentors">No mentors found</div>
            ) : (
              mentors.map((mentor) => (
                <div key={mentor.id} className="mentor mentor-card">
                  <div className="mentor-image">
                    <img
                      src={mentor.profile.imageUrl}
                      alt={mentor.profile.name}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://placehold.co/500x500.jpg?text=MENTOR';
                      }}
                    />
                  </div>
                  <div className="mentor-info">
                    <h3>{mentor.profile.name}</h3>
                    <p className="mentor-bio">{mentor.profile.bio}</p>
                    <div className="mentor-skills">
                      {mentor.profile.skills.map((skill, index) => (
                        <span key={index} className="skill-tag">{skill}</span>
                      ))}
                    </div>
                  </div>
                  <div className="mentor-request">
                    <textarea
                      id="message"
                      data-mentor-id={mentor.id}
                      data-testid={`message-${mentor.id}`}
                      value={requestMessages[mentor.id] || ''}
                      onChange={(e) => setRequestMessages(prev => ({
                        ...prev,
                        [mentor.id]: e.target.value
                      }))}
                      placeholder="Write a message to this mentor..."
                      rows={3}
                    />
                    <button
                      id="request"
                      onClick={() => handleSendRequest(mentor.id)}
                      disabled={!requestMessages[mentor.id]?.trim() || sendingRequest[mentor.id]}
                      className="request-button"
                    >
                      {sendingRequest[mentor.id] ? 'Sending...' : 'Send Request'}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Mentors;
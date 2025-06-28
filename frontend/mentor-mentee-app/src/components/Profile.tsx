import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI } from '../services/api';
import { MentorProfile, MenteeProfile } from '../types';
import './Profile.css';

const Profile: React.FC = () => {
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState({
    id: user?.id || 0,
    name: user?.profile.name || '',
    role: user?.role || 'mentee',
    bio: user?.profile.bio || '',
    image: '',
    skills: (user?.role === 'mentor' && 'skills' in user.profile) ? user.profile.skills : [],
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (name === 'skills') {
      // 스킬 입력 처리
      const skills = value.split(',').map(skill => skill.trim()).filter(skill => skill);
      setFormData(prev => ({
        ...prev,
        skills,
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 파일 크기 체크 (1MB)
    if (file.size > 1024 * 1024) {
      setError('이미지 크기는 1MB 이하여야 합니다');
      return;
    }

    // 파일 형식 체크
    if (!file.type.match(/^image\/(jpeg|jpg|png)$/)) {
      setError('JPG와 PNG 이미지만 허용됩니다');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const base64String = reader.result as string;
      const base64Data = base64String.split(',')[1]; // Remove data:image/...;base64, prefix
      setFormData(prev => ({
        ...prev,
        image: base64Data,
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await userAPI.updateProfile(formData);
      setSuccess('프로필이 성공적으로 업데이트되었습니다!');
      setEditing(false);
      // 페이지 새로고침으로 업데이트된 정보 반영
      window.location.reload();
    } catch (err: any) {
      setError(err.response?.data?.detail || '프로필 업데이트에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  const profileImageUrl = user.profile.imageUrl.startsWith('http') 
    ? user.profile.imageUrl 
    : `http://localhost:8080${user.profile.imageUrl}`;

  return (
    <div className="page-container">
      <div className="profile-container">
        <div className="profile-header">
          <div className="profile-image-container">
            <img
              id="profile-photo"
              src={profileImageUrl}
              alt="Profile"
              className="profile-image"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = user.role === 'mentor' 
                  ? 'https://placehold.co/500x500.jpg?text=MENTOR'
                  : 'https://placehold.co/500x500.jpg?text=MENTEE';
              }}
            />
            {editing && (
              <div className="image-upload">
                <input
                  type="file"
                  id="profile"
                  ref={fileInputRef}
                  accept=".jpg,.jpeg,.png"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="upload-button"
                >
                  사진 변경
                </button>
              </div>
            )}
          </div>
          
          <div className="profile-info">
            <h1>{user.profile.name}</h1>
            <p className="role-badge">{user.role.toUpperCase()}</p>
            <p className="email">{user.email}</p>
          </div>
        </div>

        <div className="profile-content">
          {editing ? (
            <form className="profile-form">
              <div className="form-group">
                <label htmlFor="name">이름</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="bio">자기소개</label>
                <textarea
                  id="bio"
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  rows={4}
                  placeholder="자신에 대해 소개해주세요..."
                />
              </div>

              {user.role === 'mentor' && (
                <div className="form-group">
                  <label htmlFor="skillsets">기술 스택 (쉼표로 구분)</label>
                  <input
                    type="text"
                    id="skillsets"
                    name="skills"
                    value={Array.isArray(formData.skills) ? formData.skills.join(', ') : ''}
                    onChange={handleInputChange}
                    placeholder="예: React, Node.js, Python"
                  />
                </div>
              )}

              <div className="form-group">
                <label htmlFor="profile">프로필 이미지</label>
                <input
                  type="file"
                  id="profile"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".png,.jpg,.jpeg"
                  style={{ display: 'none' }}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="file-button"
                >
                  이미지 선택
                </button>
                {formData.image && (
                  <span className="file-selected">새 이미지가 선택되었습니다</span>
                )}
              </div>

              <div className="form-actions">
                <button 
                  type="button" 
                  id="save"
                  onClick={handleSave} 
                  disabled={loading}
                  className="save-button"
                >
                  {loading ? '저장 중...' : '변경사항 저장'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setEditing(false)}
                  className="cancel-button"
                >
                  취소
                </button>
              </div>
            </form>
          ) : (
            <div className="profile-view">
              <div className="profile-field">
                <h3>자기소개</h3>
                <p>{user.profile.bio || '등록된 자기소개가 없습니다'}</p>
              </div>

              {user.role === 'mentor' && 'skills' in user.profile && (
                <div className="profile-field">
                  <h3>기술 스택</h3>
                  <div className="skills-list">
                    {user.profile.skills.length > 0 ? (
                      user.profile.skills.map((skill, index) => (
                        <span key={index} className="skill-tag">{skill}</span>
                      ))
                    ) : (
                      <p>등록된 기술 스택이 없습니다</p>
                    )}
                  </div>
                </div>
              )}

              <button 
                onClick={() => setEditing(true)}
                className="edit-button"
              >
                프로필 수정
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
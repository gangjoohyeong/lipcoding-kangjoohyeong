export interface User {
  id: number;
  email: string;
  role: 'mentor' | 'mentee';
  profile: MentorProfile | MenteeProfile;
}

export interface MentorProfile {
  name: string;
  bio: string;
  imageUrl: string;
  skills: string[];
}

export interface MenteeProfile {
  name: string;
  bio: string;
  imageUrl: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
  role: 'mentor' | 'mentee';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
}

export interface MatchRequest {
  id: number;
  mentorId: number;
  menteeId: number;
  message: string;
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled';
}

export interface MentorListItem {
  id: number;
  email: string;
  role: 'mentor';
  profile: MentorProfile;
}
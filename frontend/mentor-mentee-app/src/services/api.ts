import axios from 'axios';
import { SignupRequest, LoginRequest, LoginResponse, User, MentorListItem } from '../types';

const API_BASE_URL = 'http://localhost:8080/api';

// Axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 토큰 인터셉터 설정
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API 함수들
export const authAPI = {
  signup: async (data: SignupRequest): Promise<void> => {
    await apiClient.post('/signup', data);
  },

  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/login', data);
    return response.data;
  },
};

export const userAPI = {
  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/me');
    return response.data;
  },

  updateProfile: async (data: any): Promise<User> => {
    const response = await apiClient.put<User>('/profile', data);
    return response.data;
  },
};

export const mentorAPI = {
  getMentors: async (skill?: string, orderBy?: string): Promise<MentorListItem[]> => {
    const params = new URLSearchParams();
    if (skill) params.append('skill', skill);
    if (orderBy) params.append('orderBy', orderBy);
    
    const response = await apiClient.get<MentorListItem[]>(`/mentors?${params.toString()}`);
    return response.data;
  },
};

export const matchRequestAPI = {
  create: async (data: { mentorId: number; menteeId: number; message: string }) => {
    const response = await apiClient.post('/match-requests', data);
    return response.data;
  },

  getIncoming: async () => {
    const response = await apiClient.get('/match-requests/incoming');
    return response.data;
  },

  getOutgoing: async () => {
    const response = await apiClient.get('/match-requests/outgoing');
    return response.data;
  },

  accept: async (id: number) => {
    const response = await apiClient.put(`/match-requests/${id}/accept`);
    return response.data;
  },

  reject: async (id: number) => {
    const response = await apiClient.put(`/match-requests/${id}/reject`);
    return response.data;
  },

  cancel: async (id: number) => {
    const response = await apiClient.delete(`/match-requests/${id}`);
    return response.data;
  },
};
/**
 * College Student Management System (SMS) - API Client
 * Interacts with Django REST Framework backend with JWT auth and auto-refresh.
 */

const API_BASE = 'http://127.0.0.1:8000/api';

class ApiClient {
  constructor() {
    this.accessToken = localStorage.getItem('sms_access_token') || null;
    this.refreshToken = localStorage.getItem('sms_refresh_token') || null;
    this.user = JSON.parse(localStorage.getItem('sms_user') || 'null');
  }

  setSession(access, refresh, user) {
    this.accessToken = access;
    this.refreshToken = refresh;
    this.user = user;
    localStorage.setItem('sms_access_token', access);
    localStorage.setItem('sms_refresh_token', refresh);
    localStorage.setItem('sms_user', JSON.stringify(user));
  }

  clearSession() {
    this.accessToken = null;
    this.refreshToken = null;
    this.user = null;
    localStorage.removeItem('sms_access_token');
    localStorage.removeItem('sms_refresh_token');
    localStorage.removeItem('sms_user');
  }

  isAuthenticated() {
    return Boolean(this.accessToken);
  }

  getUserRole() {
    return this.user ? this.user.role : null;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    let response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch (err) {
      throw new Error(`Network error connecting to backend API at ${API_BASE}. Ensure the Django server is running.`);
    }

    // Handle token expiration & automatic refresh
    if (response.status === 401 && this.refreshToken && !endpoint.includes('/auth/refresh/')) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        return fetch(url, { ...options, headers }).then(res => this.handleResponse(res));
      } else {
        this.clearSession();
        window.dispatchEvent(new CustomEvent('sms:auth-lost'));
        throw new Error('Session expired. Please log in again.');
      }
    }

    return this.handleResponse(response);
  }

  async handleResponse(response) {
    if (response.status === 204) {
      return null;
    }
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      let errorMessage = 'An error occurred';
      if (typeof data === 'object' && data !== null) {
        if (data.detail) {
          errorMessage = data.detail;
        } else {
          // Combine serializer field errors
          errorMessage = Object.entries(data)
            .map(([field, errs]) => `${field}: ${Array.isArray(errs) ? errs.join(', ') : errs}`)
            .join(' | ');
        }
      }
      const error = new Error(errorMessage);
      error.data = data;
      error.status = response.status;
      throw error;
    }
    return data;
  }

  async login(username, password) {
    const data = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setSession(data.access, data.refresh, data.user);
    return data;
  }

  async refreshTokens() {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: this.refreshToken }),
      });
      if (res.ok) {
        const data = await res.json();
        this.accessToken = data.access;
        localStorage.setItem('sms_access_token', data.access);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  async logout() {
    if (this.refreshToken) {
      try {
        await this.request('/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh: this.refreshToken }),
        });
      } catch (err) {
        console.warn('Logout blacklist warning:', err.message);
      }
    }
    this.clearSession();
  }

  async getMe() {
    return this.request('/auth/me/');
  }

  async getDashboardSummary() {
    return this.request('/dashboard/summary/');
  }

  // Students
  async getStudents(search = '', program = '') {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (program) params.append('program', program);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/students/${query}`);
  }

  async getStudent(id) {
    return this.request(`/students/${id}/`);
  }

  async getStudentGrades(studentId) {
    return this.request(`/students/${studentId}/grades/`);
  }

  async createStudent(payload) {
    return this.request('/students/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateStudent(id, payload) {
    return this.request(`/students/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteStudent(id) {
    return this.request(`/students/${id}/`, {
      method: 'DELETE',
    });
  }

  // Subjects
  async getSubjects(search = '') {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/subjects/${query}`);
  }

  async createSubject(payload) {
    return this.request('/subjects/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateSubject(id, payload) {
    return this.request(`/subjects/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteSubject(id) {
    return this.request(`/subjects/${id}/`, {
      method: 'DELETE',
    });
  }

  // Grades
  async getGrades(studentId = '', subjectId = '') {
    const params = new URLSearchParams();
    if (studentId) params.append('student', studentId);
    if (subjectId) params.append('subject', subjectId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/grades/${query}`);
  }

  async createGrade(payload) {
    return this.request('/grades/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateGrade(id, payload) {
    return this.request(`/grades/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteGrade(id) {
    return this.request(`/grades/${id}/`, {
      method: 'DELETE',
    });
  }
}

const api = new ApiClient();
window.api = api;

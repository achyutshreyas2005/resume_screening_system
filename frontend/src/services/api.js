import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

// ── Auto-attach token to every request ────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});


// ── Auth ───────────────────────────────────────────────────────────────────────
export const registerUser = async (name, email, password) => {
  const res = await api.post('/register', { name, email, password });
  return res.data;
};

export const loginUser = async (email, password) => {
  const res = await api.post('/login', { email, password });
  return res.data;
};

export const getMe = async () => {
  const res = await api.get('/me');
  return res.data;
};


// ── Screening ──────────────────────────────────────────────────────────────────
export const screenCandidates = async (formData) => {
  const res = await api.post('/screen-with-jd-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const getCandidates = async () => {
  const res = await api.get('/candidates');
  return res.data;
};

export const getAnalytics = async () => {
  const candidates = await getCandidates();
  if (!candidates.length) return null;

  const scores    = candidates.map(c => c.score);
  const allSkills = candidates.flatMap(c => c.skills);
  const skillCount = {};
  allSkills.forEach(s => { skillCount[s] = (skillCount[s] || 0) + 1; });

  return {
    total:       candidates.length,
    average:     (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1),
    highest:     Math.max(...scores),
    shortlisted: candidates.filter(c => c.status === 'Shortlisted').length,
    in_review:   candidates.filter(c => c.status === 'In Review').length,
    rejected:    candidates.filter(c => c.status === 'Rejected').length,
    top_skills:  Object.entries(skillCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([skill, count]) => ({ skill, count })),
    candidates,
  };
};

export default api;
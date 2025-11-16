import axios from 'axios';
// Allow reading CRA env at type level without adding @types/node
declare const process: any;

// Compute API base URL robustly across environments
const getApiBaseUrl = () => {
  // 1) Explicit override via env (CRA) or global
  const explicit = (window as any).__API_BASE_URL__ || process.env.REACT_APP_API_BASE_URL;
  if (explicit && typeof explicit === 'string') {
    return explicit.replace(/\/$/, '');
  }

  // 2) GitHub Codespaces style subdomain port mapping
  if (window.location.hostname.includes('github.dev')) {
    const baseUrl = window.location.origin.replace('-3000.', '-5000.');
    return `${baseUrl}/api`;
  }

  // 3) If served over http(s), prefer same-origin API
  if (window.location.origin.startsWith('http')) {
    return `${window.location.origin}/api`;
  }

  // 4) Fallback to localhost (useful when opening file:// build directly)
  return 'http://localhost:5000/api';
};

const API_BASE_URL = getApiBaseUrl();

// Debug logging
console.log('API Base URL:', API_BASE_URL);
console.log('Window location:', window.location.href);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Add request/response interceptors for debugging
api.interceptors.request.use(
  (config: any) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, 'Full URL:', config.baseURL + config.url);
    return config;
  },
  (error: any) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response: any) => {
    console.log('API Response:', response.config.url, 'Status:', response.status);
    return response;
  },
  (error: any) => {
    console.error('API Response Error:', {
      url: error.config?.url,
      message: error.message,
      code: error.code,
      response: error.response?.data
    });
    return Promise.reject(error);
  }
);

// Teams
export const getTeams = () => api.get('/teams');
export const getTeam = (id: number) => api.get(`/teams/${id}`);

// Games
export const createGame = (data: {
  home_team_id: number;
  away_team_id: number;
  quarter_number: number;
  home_score: number;
  away_score: number;
  series_id?: number;
}) => api.post('/games/create', data);

export const getGame = (id: number) => api.get(`/games/${id}`);
export const getGames = () => api.get('/games');
export const getPlayByPlay = (gameId: number) => api.get(`/games/${gameId}/playbyplay`);

// Tournament
export const initializeTournament = () => api.post('/tournament/initialize');
export const getTournamentOverview = () => api.get('/tournament/overview');
export const getSeries = (id: number) => api.get(`/tournament/series/${id}`);
export const getActiveSeries = () => api.get('/tournament/active-series');
export const advanceRound = (roundNumber: number) => api.post(`/tournament/advance-round/${roundNumber}`);

// Stats
export const getPlayerStats = (playerId: number) => api.get(`/stats/player/${playerId}`);

export default api;

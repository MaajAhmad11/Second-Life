import axios from 'axios';

// Sanitize base URL to ensure valid requests in both local dev and production
export const getBaseURL = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;

  if (
    envUrl &&
    !envUrl.includes('<your-render-url>') &&
    !envUrl.includes('placeholder')
  ) {
    return envUrl;
  }

  // When in Vite local development OR running on Vercel (*.vercel.app),
  // use same-origin '/api' so vercel.json proxies requests directly to Render
  // without CORS or preflight issues.
  if (
    import.meta.env.DEV ||
    (typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' ||
       window.location.hostname.endsWith('.vercel.app') ||
       window.location.hostname.includes('vercel.app')))
  ) {
    return '/api';
  }

  return 'https://second-life-e45t.onrender.com/api';
};

const api = axios.create({
  baseURL: getBaseURL(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================
// Request interceptor
// ============================================================

api.interceptors.request.use(
  (config) => {
    // The chatbot endpoint is public and does not require credentials.
    // Strip Authorization to prevent 401s from stale/expired tokens in localStorage.
    if (config.url && config.url.includes('/chat')) {
      if (config.headers) {
        delete config.headers.Authorization;
      }
      return config;
    }

    const token = localStorage.getItem('secondlife_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // When sending FormData, let the browser/Axios set the
    // correct multipart Content-Type including the boundary.
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================================
// Response interceptor
// Handles expired access tokens
// ============================================================

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    if (
      error.response &&
      error.response.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem(
        'secondlife_refresh_token'
      );

      if (refreshToken) {
        try {
          const res = await axios.post(
            `${getBaseURL()}/auth/refresh/`,
            {
              refresh: refreshToken,
            }
          );

          const newAccess = res.data.access;

          localStorage.setItem(
            'secondlife_token',
            newAccess
          );

          api.defaults.headers.common.Authorization =
            `Bearer ${newAccess}`;

          originalRequest.headers.Authorization =
            `Bearer ${newAccess}`;

          return api(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('secondlife_token');
          localStorage.removeItem('secondlife_refresh_token');
          localStorage.removeItem('secondlife_user');

          window.location.replace('/login');

          return Promise.reject(refreshErr);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
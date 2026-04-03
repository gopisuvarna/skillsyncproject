import axios, { AxiosInstance } from 'axios';

const baseURL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

// ── redirect helper ────────────────────────────────────────────────
function redirectToLogin() {
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
}

// ── response interceptor ───────────────────────────────────────────
// Catches 401 (expired token) and 403 (auth failed) from any API call.
// Tries to silently refresh once. If refresh also fails → login page.
let isRefreshing = false;
let refreshQueue: Array<() => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err.response?.status;

    if ((status === 401 || status === 403) && !err.config?._retry) {
      // If already refreshing, queue this request to retry after
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push(() => resolve(api.request({ ...err.config, _retry: true })));
        });
      }

      err.config._retry = true;
      isRefreshing = true;

      try {
        await api.post('/auth/refresh/');
        // Flush queued requests
        refreshQueue.forEach((cb) => cb());
        refreshQueue = [];
        return api.request(err.config);
      } catch {
        // Refresh token also expired → force logout
        refreshQueue = [];
        redirectToLogin();
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(err);
  }
);

// ── proactive check when user returns to tab ───────────────────────
// If the user leaves the page for longer than access token lifetime
// (900s), silently try to refresh when they come back.
// If refresh fails → redirect immediately before any API call is made.
if (typeof window !== 'undefined') {
  const checkSessionOnFocus = async () => {
    try {
      await api.get('/auth/me/');
    } catch {
      // /auth/me/ will trigger the interceptor above which handles redirect
    }
  };

  // Tab becomes visible again (user switches back)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      checkSessionOnFocus();
    }
  });

  // Window regains focus
  window.addEventListener('focus', checkSessionOnFocus);
}

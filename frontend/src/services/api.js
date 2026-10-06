// Production-safe API Base URL Resolver for AutoViva Frontend

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export function getApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return API_BASE ? `${API_BASE}${cleanPath}` : cleanPath;
}

export function getAuthHeaders() {
  const token = localStorage.getItem('autoviva_token') ||
                localStorage.getItem('autoviva_jwt_token') ||
                sessionStorage.getItem('autoviva_token') ||
                sessionStorage.getItem('autoviva_jwt_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export function formatPublicationDate(dateStr) {
  if (!dateStr) return 'Recently Published';
  try {
    const cleanStr = String(dateStr).trim().replace(' ', 'T');
    const d = new Date(cleanStr);
    if (isNaN(d.getTime())) return String(dateStr);
    const day = String(d.getDate()).padStart(2, '0');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[d.getMonth()];
    const year = d.getFullYear();
    return `${day} ${month} ${year}`;
  } catch (e) {
    return String(dateStr);
  }
}

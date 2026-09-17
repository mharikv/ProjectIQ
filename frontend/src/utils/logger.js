const PREFIX = '[ProjectIQ]';

export const log = {
  info: (...args) => console.info(PREFIX, ...args),
  warn: (...args) => console.warn(PREFIX, ...args),
  error: (...args) => console.error(PREFIX, ...args),
  apiError: (action, err) => {
    const detail = err?.response?.data?.detail;
    const message = typeof detail === 'string' ? detail : err?.message || 'Unknown error';
    console.error(PREFIX, `${action} failed:`, message, err?.response?.status || '');
    return message;
  },
};

export function getApiErrorMessage(err, fallback = 'An unexpected error occurred') {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ');
  return err?.message || fallback;
}

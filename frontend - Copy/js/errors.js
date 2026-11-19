import { ApiError } from './api.js';

/**
 * Turn any thrown value into a user-facing message. Centralises the error states
 * the frontend must handle: 401, 403, 422, 500, backend unavailable and
 * database unavailable (503).
 */
export function describeApiError(error) {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 0:
        return 'Cannot reach the backend. Make sure it is running.';
      case 401:
        return error.message || 'Your session has expired. Please sign in again.';
      case 403:
        return 'You do not have permission to do that.';
      case 422:
        return 'Please check the form and try again.';
      case 503:
        return 'The service is temporarily unavailable. Please try again shortly.';
      default:
        return error.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Something went wrong. Please try again.';
}

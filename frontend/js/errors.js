import { ApiError } from './api.js';
import { t } from './i18n.js';

/**
 * Turn any thrown value into a user-facing message in the current language.
 * Known backend error codes (`errors.<CODE>`) and statuses are translated; an
 * unknown code falls back to localized status or generic text.
 */
export function describeApiError(error) {
  if (error instanceof ApiError) {
    if (error.status === 0) return t('errors.network');
    const byCode = error.code ? `errors.${error.code}` : '';
    if (byCode && t(byCode) !== byCode) return t(byCode);
    switch (error.status) {
      case 401:
        return t('errors.401');
      case 403:
        return t('errors.403');
      case 404:
        return t('errors.404');
      case 422:
        return t('errors.422');
      case 429:
        return t('errors.429');
      case 503:
        return t('errors.503');
      default:
        return t(error.status >= 500 ? 'errors.500' : 'errors.unknown');
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return t('errors.unknown');
}

import axios from 'axios';

/**
 * Parses and formats Axios error responses into user-friendly Vietnamese messages.
 */
export const getApiErrorMessage = (error: any, fallbackMessage = 'Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.'): string => {
  if (!error) return fallbackMessage;

  if (axios.isAxiosError(error)) {
    // Network error (no response received)
    if (!error.response) {
      return 'Không thể kết nối tới máy chủ. Vui lòng kiểm tra lại kết nối mạng.';
    }

    const status = error.response.status;
    const data = error.response.data;

    // Prioritize backend detail message if present
    if (data && typeof data === 'object') {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        // Validation errors e.g. pydantic errors
        const firstErr = data.detail[0];
        if (firstErr && typeof firstErr === 'object' && firstErr.msg) {
          return `Dữ liệu không hợp lệ: ${firstErr.msg}`;
        }
      }
    }

    switch (status) {
      case 400:
        return 'Yêu cầu không hợp lệ. Vui lòng kiểm tra lại thông tin gửi đi.';
      case 401:
        // Already handled by Auth Interceptor (clears token, redirects to login), 
        // return an empty message or basic text to avoid duplicate notices.
        return '';
      case 403:
        return 'Bạn không có quyền truy cập dữ liệu này.';
      case 404:
        return 'Không tìm thấy dữ liệu yêu cầu.';
      case 500:
        return 'Máy chủ đang gặp lỗi. Vui lòng thử lại sau.';
      default:
        return fallbackMessage;
    }
  }

  return error.message || fallbackMessage;
};

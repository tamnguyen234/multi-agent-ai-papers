import client from './client';
import type { UserResponse } from './authApi';

export interface NotificationUpdatePayload {
  noti_daily: boolean;
}

export const userApi = {
  updateNotification: async (noti_daily: boolean): Promise<UserResponse> => {
    const response = await client.patch<UserResponse>('/users/me/notification', {
      noti_daily,
    });
    return response.data;
  },
};

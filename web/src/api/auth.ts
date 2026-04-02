import apiClient from './client';
import type { SelectFacilityResponse, SessionLoginResponse } from '../types/wms';

export async function sessionLogin(fcmToken: string = ''): Promise<SessionLoginResponse> {
  const resp = await apiClient.post('/mobile/session/login', {
    fcm_token: fcmToken,
    device_type: 'WEB',
  });
  return resp.data;
}

export async function selectFacility(facilityId: string): Promise<SelectFacilityResponse> {
  const resp = await apiClient.post('/mobile/session/select-facility', {
    facility_id: facilityId,
  });
  return resp.data;
}

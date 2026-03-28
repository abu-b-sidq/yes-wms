import apiClient from './client';

export interface Facility {
  id: string;
  code: string;
  name: string;
  warehouse_key: string;
}

export interface SessionLoginResponse {
  data: {
    user_id: string;
    email: string;
    display_name: string;
    photo_url: string;
    last_used_facility: Facility | null;
    available_facilities: Facility[];
  };
}

export interface SelectFacilityResponse {
  data: {
    facility: Facility;
    warehouse_key: string;
    org_id: string;
  };
}

export async function sessionLogin(
  fcmToken?: string,
  deviceType: string = 'ANDROID'
): Promise<SessionLoginResponse> {
  return apiClient.post('/mobile/session/login', {
    fcm_token: fcmToken || null,
    device_type: deviceType,
  });
}

export async function selectFacility(
  facilityId: string
): Promise<SelectFacilityResponse> {
  return apiClient.post('/mobile/session/select-facility', {
    facility_id: facilityId,
  });
}

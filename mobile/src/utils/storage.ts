import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  WAREHOUSE_KEY: 'warehouse_key',
  ORG_ID: 'org_id',
  FACILITY_ID: 'facility_id',
  FACILITY_CODE: 'facility_code',
  FCM_TOKEN: 'fcm_token',
} as const;

export async function saveSessionHeaders(data: {
  warehouseKey: string;
  orgId: string;
  facilityId: string;
  facilityCode: string;
}) {
  await AsyncStorage.multiSet([
    [KEYS.WAREHOUSE_KEY, data.warehouseKey],
    [KEYS.ORG_ID, data.orgId],
    [KEYS.FACILITY_ID, data.facilityId],
    [KEYS.FACILITY_CODE, data.facilityCode],
  ]);
}

export async function getSessionHeaders(): Promise<Record<string, string>> {
  const values = await AsyncStorage.multiGet([
    KEYS.WAREHOUSE_KEY,
    KEYS.ORG_ID,
    KEYS.FACILITY_ID,
  ]);
  const headers: Record<string, string> = {};
  for (const [key, value] of values) {
    if (value) {
      if (key === KEYS.WAREHOUSE_KEY) headers['warehouse'] = value;
      if (key === KEYS.ORG_ID) headers['X-Org-Id'] = value;
      if (key === KEYS.FACILITY_ID) headers['X-Facility-Id'] = value;
    }
  }
  return headers;
}

export async function clearSession() {
  await AsyncStorage.multiRemove(Object.values(KEYS));
}

export async function saveFcmToken(token: string) {
  await AsyncStorage.setItem(KEYS.FCM_TOKEN, token);
}

export async function getFcmToken(): Promise<string | null> {
  return AsyncStorage.getItem(KEYS.FCM_TOKEN);
}

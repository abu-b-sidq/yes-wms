import axios from 'axios';
import auth from '@react-native-firebase/auth';
import { getSessionHeaders } from '../utils/storage';

const API_BASE_URL = __DEV__
  ? 'https://wms.yesworks.co.in/api/v1'
  : 'https://wms.yesworks.co.in/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

apiClient.interceptors.request.use(async (config) => {
  // Add Firebase auth token
  const user = auth().currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Add session headers (warehouse, org, facility)
  const sessionHeaders = await getSessionHeaders();
  Object.assign(config.headers, sessionHeaders);

  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    // Unwrap the envelope
    if (response.data?.success) {
      return response.data;
    }
    return response.data;
  },
  (error) => {
    const message =
      error.response?.data?.error?.message ||
      error.message ||
      'Something went wrong';
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
export { API_BASE_URL };

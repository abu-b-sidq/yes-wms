import { Vibration } from 'react-native';

const LIGHT_IMPACT_DURATION_MS = 15;
const MEDIUM_IMPACT_DURATION_MS = 25;
const SUCCESS_PATTERN = [0, 30, 40, 30];

function resolveAfterVibration(): Promise<void> {
  return Promise.resolve();
}

export function triggerLightImpact(): Promise<void> {
  Vibration.vibrate(LIGHT_IMPACT_DURATION_MS);
  return resolveAfterVibration();
}

export function triggerMediumImpact(): Promise<void> {
  Vibration.vibrate(MEDIUM_IMPACT_DURATION_MS);
  return resolveAfterVibration();
}

export function triggerSuccessNotification(): Promise<void> {
  Vibration.vibrate(SUCCESS_PATTERN);
  return resolveAfterVibration();
}

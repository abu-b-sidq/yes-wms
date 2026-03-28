export const colors = {
  // Core palette
  primary: '#6C63FF',
  primaryDark: '#5A52D5',
  primaryLight: '#8B85FF',
  secondary: '#FF6584',
  accent: '#00D9A6',
  warning: '#FFB800',

  // Backgrounds
  bg: '#0F0F1A',
  bgCard: '#1A1A2E',
  bgCardLight: '#222240',
  bgSurface: '#16213E',

  // Text
  textPrimary: '#FFFFFF',
  textSecondary: '#A0A0C0',
  textMuted: '#6C6C8A',

  // Status
  success: '#00D9A6',
  error: '#FF4757',
  pending: '#FFB800',
  inProgress: '#6C63FF',
  completed: '#00D9A6',

  // Gamification
  xpGold: '#FFD700',
  streakFire: '#FF6B35',
  levelRookie: '#A0A0C0',
  levelPro: '#6C63FF',
  levelExpert: '#FF6584',
  levelMaster: '#FFD700',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 999,
};

export const typography = {
  h1: { fontSize: 32, fontWeight: '800' as const },
  h2: { fontSize: 24, fontWeight: '700' as const },
  h3: { fontSize: 20, fontWeight: '600' as const },
  body: { fontSize: 16, fontWeight: '400' as const },
  bodyBold: { fontSize: 16, fontWeight: '600' as const },
  caption: { fontSize: 14, fontWeight: '400' as const },
  small: { fontSize: 12, fontWeight: '400' as const },
};

export const getLevelColor = (level: string) => {
  switch (level) {
    case 'MASTER': return colors.levelMaster;
    case 'EXPERT': return colors.levelExpert;
    case 'PRO': return colors.levelPro;
    default: return colors.levelRookie;
  }
};

export const getStatusColor = (status: string) => {
  switch (status) {
    case 'COMPLETED': return colors.completed;
    case 'IN_PROGRESS': return colors.inProgress;
    case 'ASSIGNED': return colors.primary;
    case 'PENDING': return colors.pending;
    case 'CANCELLED': return colors.error;
    default: return colors.textMuted;
  }
};

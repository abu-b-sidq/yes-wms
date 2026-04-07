export const colors = {
  // Core palette
  primary: '#79BF64',
  primaryDark: '#5F9F4E',
  primaryLight: '#D4EA72',
  primaryContrast: '#0F1D11',
  secondary: '#D4EA72',
  accent: '#76B0FF',
  accentViolet: '#BF9BFF',
  accentAmber: '#F2C162',
  warning: '#E4B452',

  // Backgrounds
  bg: '#081311',
  bgSoft: '#0D1D19',
  bgCard: '#112420',
  bgCardLight: '#1B3831',
  bgSurface: '#17322C',
  bgSurfaceMuted: '#1B3831',
  glass: 'rgba(10, 20, 17, 0.72)',
  glassSoft: 'rgba(255, 255, 255, 0.04)',
  overlay: 'rgba(8, 19, 17, 0.78)',

  // Text
  textPrimary: '#F3F8F2',
  textSecondary: '#B4C4BA',
  textMuted: '#7D9487',
  textSoft: '#566B61',

  // Status
  success: '#65C186',
  error: '#EF7C74',
  pending: '#E4B452',
  inProgress: '#79BF64',
  completed: '#65C186',

  // Gamification
  xpGold: '#F2C162',
  streakFire: '#EF7C74',
  levelRookie: '#A0A0C0',
  levelPro: '#79BF64',
  levelExpert: '#BF9BFF',
  levelMaster: '#D4EA72',
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
  sm: 10,
  md: 14,
  lg: 18,
  xl: 28,
  full: 999,
};

export const typography = {
  h1: { fontSize: 34, fontWeight: '800' as const },
  h2: { fontSize: 26, fontWeight: '700' as const },
  h3: { fontSize: 20, fontWeight: '600' as const },
  body: { fontSize: 16, fontWeight: '400' as const },
  bodyBold: { fontSize: 16, fontWeight: '600' as const },
  caption: { fontSize: 14, fontWeight: '400' as const },
  small: { fontSize: 12, fontWeight: '400' as const },
};

export const shadows = {
  card: {
    shadowColor: '#020B08',
    shadowOpacity: 0.24,
    shadowOffset: { width: 0, height: 14 },
    shadowRadius: 24,
    elevation: 8,
  },
  soft: {
    shadowColor: '#030D0A',
    shadowOpacity: 0.16,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 16,
    elevation: 4,
  },
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

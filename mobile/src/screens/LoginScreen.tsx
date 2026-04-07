import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  useWindowDimensions,
} from 'react-native';
import { useAuth } from '../auth/AuthContext';
import { AmbientBackdrop } from '../components/AmbientBackdrop';
import { colors, spacing, borderRadius, typography, shadows } from '../theme';

export function LoginScreen() {
  const {
    signIn,
    signInWithGoogle,
    loading,
    loginError,
    googleSignInAvailable,
    googleSignInMessage,
  } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { height } = useWindowDimensions();
  const compact = height < 820;
  const ultraCompact = height < 720;

  const handleLogin = () => {
    if (email.trim() && password.trim()) {
      signIn(email.trim(), password.trim());
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <AmbientBackdrop variant="auth" />
      <View style={[styles.content, compact && styles.contentCompact]}>
        

        <View style={[styles.formCard, compact && styles.formCardCompact]}>
          <View style={[styles.header, compact && styles.headerCompact]}>
            <View style={[styles.logoBadge, compact && styles.logoBadgeCompact]}>
              <Text style={styles.logoGlyph}>Y</Text>
            </View>
            <Text style={styles.logo}>YES WMS</Text>
            <Text style={styles.subtitle}>Operations Dashboard Theme</Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.title}>Sign In</Text>

            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor={colors.textMuted}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor={colors.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            {loginError ? (
              <View style={styles.errorBanner}>
                <Text style={styles.error}>{loginError}</Text>
              </View>
            ) : null}

            <TouchableOpacity
              style={[styles.button, (!email || !password) && styles.buttonDisabled]}
              onPress={handleLogin}
              disabled={loading || !email || !password}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color={colors.primaryContrast} />
              ) : (
                <Text style={styles.buttonText}>Sign In</Text>
              )}
            </TouchableOpacity>

            <View style={styles.dividerRow}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.divider} />
            </View>

            <TouchableOpacity
              style={[
                styles.googleButton,
                (!googleSignInAvailable || loading) && styles.buttonDisabled,
              ]}
              onPress={signInWithGoogle}
              disabled={loading || !googleSignInAvailable}
              activeOpacity={0.8}
            >
              <View style={styles.googleIcon}>
                <Text style={styles.googleIconText}>G</Text>
              </View>
              <Text style={styles.googleButtonText}>Continue with Google</Text>
            </TouchableOpacity>

            {!googleSignInAvailable ? (
              <Text style={styles.helperText}>
                {googleSignInMessage || 'Google sign-in is unavailable in this build.'}
              </Text>
            ) : null}
          </View>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: spacing.lg,
    paddingVertical: spacing.xl,
    gap: spacing.md,
  },
  contentCompact: {
    paddingVertical: spacing.md,
    gap: spacing.sm,
  },
  heroCard: {
    backgroundColor: colors.glass,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    marginBottom: spacing.lg,
    ...shadows.card,
  },
  heroCardCompact: {
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  heroEyebrow: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs + 2,
    borderRadius: borderRadius.full,
    backgroundColor: colors.secondary + '24',
    borderWidth: 1,
    borderColor: colors.secondary + '36',
  },
  heroEyebrowText: {
    ...typography.small,
    color: colors.secondary,
    fontWeight: '700',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  heroTitle: {
    ...typography.h1,
    color: colors.textPrimary,
    marginTop: spacing.md,
    lineHeight: 38,
  },
  heroTitleCompact: {
    fontSize: 28,
    lineHeight: 32,
    marginTop: spacing.sm,
  },
  heroText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    lineHeight: 24,
  },
  heroTextCompact: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: spacing.xs,
  },
  heroPills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  heroPill: {
    paddingHorizontal: spacing.sm + 4,
    paddingVertical: spacing.xs + 4,
    borderRadius: borderRadius.full,
    backgroundColor: colors.glassSoft,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  heroPillText: {
    ...typography.small,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  formCard: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.card,
  },
  formCardCompact: {
    padding: spacing.md,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  headerCompact: {
    marginBottom: spacing.md,
  },
  logoBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  logoBadgeCompact: {
    width: 56,
    height: 56,
    borderRadius: 28,
    marginBottom: spacing.sm,
  },
  logoGlyph: {
    fontSize: 34,
    fontWeight: '800',
    color: colors.primaryContrast,
  },
  logo: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: 1,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  form: {
    gap: spacing.sm,
  },
  title: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  input: {
    backgroundColor: colors.bgSurface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    ...typography.body,
    color: colors.textPrimary,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  errorBanner: {
    backgroundColor: colors.error + '18',
    borderWidth: 1,
    borderColor: colors.error + '24',
    borderRadius: borderRadius.md,
    padding: spacing.sm + 2,
  },
  error: {
    ...typography.caption,
    color: colors.error,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.sm,
    ...shadows.soft,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    ...typography.bodyBold,
    color: colors.primaryContrast,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: colors.bgCardLight,
  },
  dividerText: {
    ...typography.caption,
    color: colors.textMuted,
    marginHorizontal: spacing.md,
  },
  googleButton: {
    backgroundColor: colors.bgSoft,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  googleIcon: {
    width: 24,
    height: 24,
    borderRadius: borderRadius.full,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleIconText: {
    ...typography.bodyBold,
    color: colors.bg,
  },
  googleButtonText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  helperText: {
    ...typography.small,
    color: colors.textMuted,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
});

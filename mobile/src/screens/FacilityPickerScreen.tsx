import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../auth/AuthContext';
import { Facility } from '../api/auth';
import { AmbientBackdrop } from '../components/AmbientBackdrop';
import { colors, spacing, borderRadius, typography, shadows } from '../theme';

export function FacilityPickerScreen() {
  const { facilities, chooseFacility, loading, signOut } = useAuth();

  const renderFacility = ({ item }: { item: Facility }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => chooseFacility(item)}
      activeOpacity={0.7}
    >
      <View style={styles.iconContainer}>
        <Text style={styles.icon}>🏭</Text>
      </View>
      <View style={styles.info}>
        <Text style={styles.name}>{item.name}</Text>
        <Text style={styles.code}>{item.code}</Text>
      </View>
      <Text style={styles.arrow}>›</Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.screen}>
        <AmbientBackdrop variant="auth" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <AmbientBackdrop variant="auth" />
      <View style={styles.container}>
        <View style={styles.facilityCard}>
          <View style={styles.header}>
            <View style={styles.logoBadge}>
              <Text style={styles.logoGlyph}>Y</Text>
            </View>
            <Text style={styles.title}>Select Facility</Text>
            <Text style={styles.subtitle}>Choose the warehouse to continue.</Text>
          </View>

          {facilities.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🔒</Text>
              <Text style={styles.emptyTitle}>No Access</Text>
              <Text style={styles.emptyText}>
                You don't have access to any warehouses yet.{'\n'}
                Contact your admin to get assigned.
              </Text>
            </View>
          ) : (
            <FlatList
              data={facilities}
              renderItem={renderFacility}
              keyExtractor={(item) => item.id}
              contentContainerStyle={styles.list}
            />
          )}

          <TouchableOpacity style={styles.signOutButton} onPress={signOut}>
            <Text style={styles.signOutText}>Sign Out</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: spacing.lg,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  facilityCard: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    padding: spacing.lg,
    maxHeight: '84%',
    ...shadows.card,
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  logoGlyph: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.primaryContrast,
  },
  title: {
    ...typography.h2,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  list: {
    paddingBottom: spacing.md,
  },
  card: {
    backgroundColor: colors.bgSurface,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.soft,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  icon: {
    fontSize: 24,
  },
  info: {
    flex: 1,
  },
  name: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  code: {
    ...typography.caption,
    color: colors.textMuted,
  },
  arrow: {
    fontSize: 24,
    color: colors.textMuted,
  },
  emptyState: {
    paddingVertical: spacing.xxl,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  signOutButton: {
    marginTop: spacing.sm,
    paddingVertical: spacing.md,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.bgCardLight,
  },
  signOutText: {
    ...typography.bodyBold,
    color: colors.error,
  },
});

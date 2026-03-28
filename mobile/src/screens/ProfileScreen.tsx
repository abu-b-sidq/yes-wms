import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useAuth } from '../auth/AuthContext';
import { getWorkerStats, WorkerStats } from '../api/gamification';
import { PointsBadge } from '../components/PointsBadge';
import { StreakIndicator } from '../components/StreakIndicator';
import { colors, spacing, borderRadius, typography, getLevelColor } from '../theme';

export function ProfileScreen() {
  const { user, selectedFacility, signOut } = useAuth();
  const [stats, setStats] = useState<WorkerStats | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getWorkerStats();
      setStats(result.data);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const getNextLevel = (level: string) => {
    switch (level) {
      case 'ROOKIE': return { next: 'PRO', target: 500 };
      case 'PRO': return { next: 'EXPERT', target: 2000 };
      case 'EXPERT': return { next: 'MASTER', target: 5000 };
      default: return null;
    }
  };

  const nextLevel = stats ? getNextLevel(stats.level) : null;
  const progressToNext = stats && nextLevel
    ? Math.min((stats.total_points / nextLevel.target) * 100, 100)
    : 100;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={loading}
          onRefresh={refresh}
          tintColor={colors.primary}
        />
      }
    >
      {/* Profile Header */}
      <View style={styles.profileHeader}>
        <View style={styles.avatarLarge}>
          <Text style={styles.avatarText}>
            {(user?.displayName || 'W')[0].toUpperCase()}
          </Text>
        </View>
        <Text style={styles.displayName}>
          {user?.displayName || 'Warehouse Worker'}
        </Text>
        <Text style={styles.email}>{user?.email}</Text>
        <Text style={styles.facility}>
          {selectedFacility?.name || 'No facility'}
        </Text>
      </View>

      {/* Stats */}
      {stats && (
        <>
          <View style={styles.card}>
            <PointsBadge points={stats.total_points} level={stats.level} size="large" />

            {nextLevel && (
              <View style={styles.progressContainer}>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${progressToNext}%`,
                        backgroundColor: getLevelColor(stats.level),
                      },
                    ]}
                  />
                </View>
                <Text style={styles.progressText}>
                  {stats.total_points} / {nextLevel.target} XP to {nextLevel.next}
                </Text>
              </View>
            )}
          </View>

          <View style={styles.card}>
            <StreakIndicator
              streak={stats.current_streak}
              longestStreak={stats.longest_streak}
            />
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{stats.tasks_completed}</Text>
              <Text style={styles.statLabel}>Tasks Done</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{stats.current_streak}</Text>
              <Text style={styles.statLabel}>Day Streak</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{stats.longest_streak}</Text>
              <Text style={styles.statLabel}>Best Streak</Text>
            </View>
          </View>
        </>
      )}

      {/* Sign Out */}
      <TouchableOpacity style={styles.signOutButton} onPress={signOut}>
        <Text style={styles.signOutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    padding: spacing.md,
    paddingTop: spacing.xxl + spacing.md,
    paddingBottom: spacing.xxl,
  },
  profileHeader: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  avatarLarge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  displayName: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  email: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  facility: {
    ...typography.small,
    color: colors.textMuted,
    marginTop: 2,
  },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  progressContainer: {
    marginTop: spacing.md,
  },
  progressBar: {
    height: 8,
    backgroundColor: colors.bgCardLight,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    ...typography.small,
    color: colors.textMuted,
    marginTop: spacing.xs,
    textAlign: 'center',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  statValue: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  statLabel: {
    ...typography.small,
    color: colors.textMuted,
  },
  signOutButton: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.error + '30',
  },
  signOutText: {
    ...typography.bodyBold,
    color: colors.error,
  },
});

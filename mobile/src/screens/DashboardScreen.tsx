import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth/AuthContext';
import { useTasks } from '../hooks/useTasks';
import { useWebSocket, WsEvent } from '../hooks/useWebSocket';
import { getWorkerStats, WorkerStats } from '../api/gamification';
import { PointsBadge } from '../components/PointsBadge';
import { StreakIndicator } from '../components/StreakIndicator';
import { TaskCard } from '../components/TaskCard';
import { colors, spacing, borderRadius, typography } from '../theme';

export function DashboardScreen() {
  const navigation = useNavigation<any>();
  const { user, selectedFacility, signOut } = useAuth();
  const { myPicks, myDrops, availableTasks, refresh, loading } = useTasks();
  const [stats, setStats] = useState<WorkerStats | null>(null);

  const loadStats = useCallback(async () => {
    try {
      const result = await getWorkerStats();
      setStats(result.data);
    } catch {}
  }, []);

  const handleWsEvent = useCallback(
    (event: WsEvent) => {
      if (
        event.type === 'new_task_available' ||
        event.type === 'task_claimed' ||
        event.type === 'drop_assigned'
      ) {
        refresh();
      }
      if (event.type === 'leaderboard_update') {
        loadStats();
      }
    },
    [refresh, loadStats]
  );

  const { connected } = useWebSocket(
    selectedFacility?.id || null,
    handleWsEvent
  );

  useEffect(() => {
    refresh();
    loadStats();
  }, [refresh, loadStats]);

  const activePick = myPicks.find(
    (p) => p.task_status === 'ASSIGNED' || p.task_status === 'IN_PROGRESS'
  );
  const activeDrop = myDrops.find(
    (d) => d.task_status === 'ASSIGNED' || d.task_status === 'IN_PROGRESS'
  );

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={loading}
          onRefresh={() => {
            refresh();
            loadStats();
          }}
          tintColor={colors.primary}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>
            Hey, {user?.displayName || 'Worker'} 👋
          </Text>
          <View style={styles.facilityRow}>
            <Text style={styles.facilityName}>
              {selectedFacility?.name || 'No facility'}
            </Text>
            <View
              style={[
                styles.connectionDot,
                { backgroundColor: connected ? colors.success : colors.error },
              ]}
            />
          </View>
        </View>
        <TouchableOpacity onPress={signOut} style={styles.avatarContainer}>
          <Text style={styles.avatarText}>
            {(user?.displayName || 'W')[0].toUpperCase()}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Stats Card */}
      {stats && (
        <View style={styles.statsCard}>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{stats.tasks_completed}</Text>
              <Text style={styles.statLabel}>Tasks Done</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <PointsBadge points={stats.total_points} level={stats.level} />
            </View>
          </View>
          <StreakIndicator
            streak={stats.current_streak}
            longestStreak={stats.longest_streak}
          />
        </View>
      )}

      {/* Active Task */}
      {activePick && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Active Pick Task</Text>
          <TaskCard
            type="pick"
            skuCode={activePick.sku_code}
            skuName={activePick.sku_name}
            entityCode={activePick.source_entity_code}
            quantity={activePick.quantity}
            status={activePick.task_status}
            referenceNumber={activePick.reference_number}
            onPress={() =>
              navigation.navigate('PickTask', { pick: activePick })
            }
            actionLabel={
              activePick.task_status === 'ASSIGNED'
                ? 'Start Pick'
                : 'Continue Pick'
            }
            onAction={() =>
              navigation.navigate('PickTask', { pick: activePick })
            }
          />
        </View>
      )}

      {activeDrop && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Active Drop Task</Text>
          <TaskCard
            type="drop"
            skuCode={activeDrop.sku_code}
            skuName={activeDrop.sku_name}
            entityCode={activeDrop.dest_entity_code}
            quantity={activeDrop.quantity}
            status={activeDrop.task_status}
            referenceNumber={activeDrop.reference_number}
            onPress={() =>
              navigation.navigate('DropTask', { drop: activeDrop })
            }
            actionLabel={
              activeDrop.task_status === 'ASSIGNED'
                ? 'Start Drop'
                : 'Continue Drop'
            }
            onAction={() =>
              navigation.navigate('DropTask', { drop: activeDrop })
            }
          />
        </View>
      )}

      {/* Available Tasks Preview */}
      {!activePick && !activeDrop && (
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Available Tasks</Text>
            <TouchableOpacity
              onPress={() => navigation.navigate('AvailableTasks')}
            >
              <Text style={styles.seeAll}>See all →</Text>
            </TouchableOpacity>
          </View>
          {availableTasks.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>✅</Text>
              <Text style={styles.emptyText}>
                No tasks available right now
              </Text>
            </View>
          ) : (
            availableTasks.slice(0, 3).map((task) => (
              <TaskCard
                key={task.id}
                type="pick"
                skuCode={task.sku_code}
                skuName={task.sku_name}
                entityCode={task.source_entity_code}
                quantity={task.quantity}
                status={task.task_status}
                referenceNumber={task.reference_number}
                actionLabel="Claim"
                onAction={() =>
                  navigation.navigate('AvailableTasks')
                }
              />
            ))
          )}
        </View>
      )}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  greeting: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  facilityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: 2,
  },
  facilityName: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  avatarContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    ...typography.h3,
    color: colors.textPrimary,
  },
  statsCard: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    marginBottom: spacing.lg,
    gap: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.bgCardLight,
  },
  statValue: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  statLabel: {
    ...typography.small,
    color: colors.textMuted,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  seeAll: {
    ...typography.caption,
    color: colors.primary,
  },
  emptyState: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
  },
  emptyEmoji: {
    fontSize: 32,
    marginBottom: spacing.sm,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
  },
});

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
import { DropTask, PickTask } from '../api/tasks';
import { getWorkerStats, WorkerStats } from '../api/gamification';
import { AmbientBackdrop } from '../components/AmbientBackdrop';
import { PointsBadge } from '../components/PointsBadge';
import { StreakIndicator } from '../components/StreakIndicator';
import { TaskCard } from '../components/TaskCard';
import { colors, spacing, borderRadius, typography, shadows } from '../theme';

export function DashboardScreen() {
  const navigation = useNavigation<any>();
  const { user, selectedFacility, signOut } = useAuth();
  const { myPicks, myDrops, availablePicks, availableDrops, refresh, loading } = useTasks();
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
  const availableTasks = [
    ...availablePicks.map((task) => ({ type: 'pick' as const, task })),
    ...availableDrops.map((task) => ({ type: 'drop' as const, task })),
  ];

  return (
    <View style={styles.screen}>
      <AmbientBackdrop />
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
        <View style={styles.headerCard}>
          <View style={styles.headerTop}>
            <View style={styles.headerCopy}>
              <View style={styles.headerEyebrow}>
                <Text style={styles.headerEyebrowText}>Operations Console</Text>
              </View>
              <Text style={styles.greeting}>
                Hey, {user?.displayName || 'Worker'}
              </Text>
              <Text style={styles.headerText}>
                Keep warehouse flow moving with live task visibility.
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
                <Text style={styles.connectionText}>
                  {connected ? 'Live' : 'Offline'}
                </Text>
              </View>
            </View>
            <TouchableOpacity onPress={signOut} style={styles.avatarContainer}>
              <Text style={styles.avatarText}>
                {(user?.displayName || 'W')[0].toUpperCase()}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {stats ? (
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
        ) : null}

        {activePick ? (
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
        ) : null}

        {activeDrop ? (
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
        ) : null}

        {!activePick && !activeDrop ? (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Available Tasks</Text>
              <TouchableOpacity
                onPress={() => navigation.navigate('AvailableTasks')}
              >
                <Text style={styles.seeAll}>See all</Text>
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
              availableTasks.slice(0, 3).map((availableTask) => {
                if (availableTask.type === 'pick') {
                  const task: PickTask = availableTask.task;
                  return (
                    <TaskCard
                      key={`pick-${task.id}`}
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
                  );
                }

                const task: DropTask = availableTask.task;
                return (
                  <TaskCard
                    key={`drop-${task.id}`}
                    type="drop"
                    skuCode={task.sku_code}
                    skuName={task.sku_name}
                    entityCode={task.dest_entity_code}
                    quantity={task.quantity}
                    status={task.task_status}
                    referenceNumber={task.reference_number}
                    actionLabel="Claim"
                    onAction={() =>
                      navigation.navigate('AvailableTasks')
                    }
                  />
                );
              })
            )}
          </View>
        ) : null}
      </ScrollView>
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
    backgroundColor: 'transparent',
  },
  content: {
    padding: spacing.md,
    paddingTop: spacing.xxl + spacing.md,
    paddingBottom: spacing.xxl * 2,
  },
  headerCard: {
    backgroundColor: colors.glass,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    marginBottom: spacing.lg,
    ...shadows.card,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  headerCopy: {
    flex: 1,
  },
  headerEyebrow: {
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs + 2,
    borderRadius: borderRadius.full,
    backgroundColor: colors.secondary + '20',
    borderWidth: 1,
    borderColor: colors.secondary + '2C',
    marginBottom: spacing.sm,
  },
  headerEyebrowText: {
    ...typography.small,
    color: colors.secondary,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  greeting: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  headerText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    lineHeight: 22,
  },
  facilityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginTop: spacing.md,
  },
  facilityName: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  connectionText: {
    ...typography.small,
    color: colors.textMuted,
  },
  connectionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  avatarContainer: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    ...shadows.soft,
  },
  avatarText: {
    ...typography.h3,
    color: colors.primaryContrast,
  },
  statsCard: {
    backgroundColor: colors.bgSurface,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    marginBottom: spacing.lg,
    gap: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.card,
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
    fontWeight: '700',
  },
  emptyState: {
    backgroundColor: colors.bgSurface,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.soft,
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

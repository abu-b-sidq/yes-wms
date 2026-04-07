import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SectionList,
  RefreshControl,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTasks } from '../hooks/useTasks';
import { useWebSocket, WsEvent } from '../hooks/useWebSocket';
import { useAuth } from '../auth/AuthContext';
import { AmbientBackdrop } from '../components/AmbientBackdrop';
import { TaskCard } from '../components/TaskCard';
import { DropTask, PickTask } from '../api/tasks';
import { colors, spacing, typography, borderRadius, shadows } from '../theme';
import {
  triggerMediumImpact,
  triggerSuccessNotification,
} from '../utils/haptics';

type AvailableTaskItem =
  | { type: 'pick'; item: PickTask }
  | { type: 'drop'; item: DropTask };

type AvailableTaskSection = {
  title: string;
  data: AvailableTaskItem[];
};

export function AvailableTasksScreen() {
  const navigation = useNavigation<any>();
  const { selectedFacility } = useAuth();
  const { availablePicks, availableDrops, loading, refresh, claim, claimDrop } = useTasks();

  const handleWsEvent = useCallback(
    (event: WsEvent) => {
      if (event.type === 'new_task_available' || event.type === 'task_claimed') {
        refresh();
      }
    },
    [refresh]
  );

  useWebSocket(selectedFacility?.id || null, handleWsEvent);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleClaim = async (task: PickTask) => {
    try {
      await triggerMediumImpact();
      const claimedTask = await claim(task.id);
      await triggerSuccessNotification();
      navigation.navigate('PickTask', { pick: claimedTask });
    } catch (err: any) {
      Alert.alert('Cannot Claim', err.message || 'Task may have been claimed by someone else.');
    }
  };

  const handleClaimDrop = async (task: DropTask) => {
    try {
      await triggerMediumImpact();
      const claimedTask = await claimDrop(task.id);
      await triggerSuccessNotification();
      navigation.navigate('DropTask', { drop: claimedTask });
    } catch (err: any) {
      Alert.alert('Cannot Claim', err.message || 'Task may have been claimed by someone else.');
    }
  };

  const sections: AvailableTaskSection[] = [
    ...(availablePicks.length > 0
      ? [{ title: 'Available Picks', data: availablePicks.map((pick) => ({ type: 'pick' as const, item: pick })) }]
      : []),
    ...(availableDrops.length > 0
      ? [{ title: 'Available Drops', data: availableDrops.map((drop) => ({ type: 'drop' as const, item: drop })) }]
      : []),
  ];
  const totalTasks = availablePicks.length + availableDrops.length;

  return (
    <View style={styles.screen}>
      <AmbientBackdrop />
      <SectionList
        style={styles.container}
        sections={sections}
        renderSectionHeader={({ section }) => (
          <Text style={styles.sectionTitle}>{section.title}</Text>
        )}
        renderItem={({ item }) => {
          if (item.type === 'pick') {
            const pick = item.item;
            return (
              <TaskCard
                type="pick"
                skuCode={pick.sku_code}
                skuName={pick.sku_name}
                entityCode={pick.source_entity_code}
                quantity={pick.quantity}
                status={pick.task_status}
                batchNumber={pick.batch_number}
                referenceNumber={pick.reference_number}
                actionLabel="Claim Task"
                onAction={() => handleClaim(pick)}
              />
            );
          }

          const drop = item.item;
          return (
            <TaskCard
              type="drop"
              skuCode={drop.sku_code}
              skuName={drop.sku_name}
              entityCode={drop.dest_entity_code}
              quantity={drop.quantity}
              status={drop.task_status}
              batchNumber={drop.batch_number}
              referenceNumber={drop.reference_number}
              actionLabel="Claim Task"
              onAction={() => handleClaimDrop(drop)}
            />
          );
        }}
        keyExtractor={(item) => `${item.type}-${item.item.id}`}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refresh}
            tintColor={colors.primary}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>📭</Text>
            <Text style={styles.emptyTitle}>No Tasks Available</Text>
            <Text style={styles.emptyText}>
              Pull down to refresh or wait for new tasks
            </Text>
          </View>
        }
        ListHeaderComponent={
          <View style={styles.countCard}>
            <Text style={styles.countEyebrow}>Live Queue</Text>
            <Text style={styles.count}>
              {totalTasks} task{totalTasks !== 1 ? 's' : ''} available
            </Text>
          </View>
        }
      />
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
  list: {
    padding: spacing.md,
    paddingBottom: spacing.xxl * 2,
  },
  countCard: {
    backgroundColor: colors.glass,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  countEyebrow: {
    ...typography.small,
    color: colors.secondary,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  count: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    marginTop: spacing.xs,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
  },
  emptyState: {
    backgroundColor: colors.bgSurface,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    alignItems: 'center',
    padding: spacing.xl,
    ...shadows.soft,
  },
  emptyEmoji: {
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
});

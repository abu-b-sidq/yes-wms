import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  Alert,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { useNavigation } from '@react-navigation/native';
import { useTasks } from '../hooks/useTasks';
import { useWebSocket, WsEvent } from '../hooks/useWebSocket';
import { useAuth } from '../auth/AuthContext';
import { TaskCard } from '../components/TaskCard';
import { PickTask } from '../api/tasks';
import { colors, spacing, typography } from '../theme';

export function AvailableTasksScreen() {
  const navigation = useNavigation<any>();
  const { selectedFacility } = useAuth();
  const { availableTasks, loading, refresh, claim } = useTasks();

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
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      await claim(task.id);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      navigation.navigate('PickTask', { pick: task });
    } catch (err: any) {
      Alert.alert('Cannot Claim', err.message || 'Task may have been claimed by someone else.');
    }
  };

  const renderTask = ({ item }: { item: PickTask }) => (
    <TaskCard
      type="pick"
      skuCode={item.sku_code}
      skuName={item.sku_name}
      entityCode={item.source_entity_code}
      quantity={item.quantity}
      status={item.task_status}
      batchNumber={item.batch_number}
      referenceNumber={item.reference_number}
      actionLabel="Claim Task"
      onAction={() => handleClaim(item)}
    />
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={availableTasks}
        renderItem={renderTask}
        keyExtractor={(item) => item.id}
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
          <Text style={styles.count}>
            {availableTasks.length} task{availableTasks.length !== 1 ? 's' : ''} available
          </Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  list: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  count: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: spacing.xxl * 2,
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

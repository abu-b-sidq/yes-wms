import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SectionList,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTasks } from '../hooks/useTasks';
import { DropTask, PickTask } from '../api/tasks';
import { AmbientBackdrop } from '../components/AmbientBackdrop';
import { TaskCard } from '../components/TaskCard';
import { colors, spacing, typography, borderRadius, shadows } from '../theme';

type MyTaskItem =
  | { type: 'pick'; item: PickTask }
  | { type: 'drop'; item: DropTask };

type MyTaskSection = {
  title: string;
  data: MyTaskItem[];
};

export function MyTasksScreen() {
  const navigation = useNavigation<any>();
  const { myPicks, myDrops, loading, refresh } = useTasks();

  useEffect(() => {
    refresh();
  }, [refresh]);

  const sections: MyTaskSection[] = [
    ...(myPicks.length > 0
      ? [{ title: 'Active Picks', data: myPicks.map((p) => ({ type: 'pick' as const, item: p })) }]
      : []),
    ...(myDrops.length > 0
      ? [{ title: 'Active Drops', data: myDrops.map((d) => ({ type: 'drop' as const, item: d })) }]
      : []),
  ];

  return (
    <View style={styles.screen}>
      <AmbientBackdrop />
      <SectionList
        style={styles.container}
        sections={sections}
        keyExtractor={(item) => item.item.id}
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
                referenceNumber={pick.reference_number}
                onPress={() => navigation.navigate('PickTask', { pick })}
                actionLabel={
                  pick.task_status === 'ASSIGNED' ? 'Start' : 'Continue'
                }
                onAction={() => navigation.navigate('PickTask', { pick })}
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
              referenceNumber={drop.reference_number}
              onPress={() => navigation.navigate('DropTask', { drop })}
              actionLabel={
                drop.task_status === 'ASSIGNED' ? 'Start' : 'Continue'
              }
              onAction={() => navigation.navigate('DropTask', { drop })}
            />
          );
        }}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refresh}
            tintColor={colors.primary}
          />
        }
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <View style={styles.summaryCard}>
            <Text style={styles.summaryEyebrow}>Assigned Work</Text>
            <Text style={styles.summaryText}>
              {myPicks.length + myDrops.length} active task{myPicks.length + myDrops.length !== 1 ? 's' : ''}
            </Text>
          </View>
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>😴</Text>
            <Text style={styles.emptyTitle}>No Active Tasks</Text>
            <Text style={styles.emptyText}>
              Claim a task from the Available tab to get started
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
  summaryCard: {
    backgroundColor: colors.glass,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  summaryEyebrow: {
    ...typography.small,
    color: colors.secondary,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  summaryText: {
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

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
import { TaskCard } from '../components/TaskCard';
import { colors, spacing, typography } from '../theme';

export function MyTasksScreen() {
  const navigation = useNavigation<any>();
  const { myPicks, myDrops, loading, refresh } = useTasks();

  useEffect(() => {
    refresh();
  }, [refresh]);

  const sections = [
    ...(myPicks.length > 0
      ? [{ title: 'Active Picks', data: myPicks.map((p) => ({ type: 'pick' as const, item: p })) }]
      : []),
    ...(myDrops.length > 0
      ? [{ title: 'Active Drops', data: myDrops.map((d) => ({ type: 'drop' as const, item: d })) }]
      : []),
  ];

  return (
    <View style={styles.container}>
      <SectionList
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
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  list: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
    marginTop: spacing.md,
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

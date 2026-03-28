import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
} from 'react-native';
import { getLeaderboard, LeaderboardEntry } from '../api/gamification';
import { colors, spacing, borderRadius, typography, getLevelColor } from '../theme';

export function LeaderboardScreen() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getLeaderboard();
      setEntries(result.data);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const getMedalEmoji = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getLevel = (points: number) => {
    if (points >= 5000) return 'MASTER';
    if (points >= 2000) return 'EXPERT';
    if (points >= 500) return 'PRO';
    return 'ROOKIE';
  };

  const renderEntry = ({ item }: { item: LeaderboardEntry }) => {
    const level = getLevel(item.total_points);
    const levelColor = getLevelColor(level);
    const isTopThree = item.rank <= 3;

    return (
      <View style={[styles.row, isTopThree && styles.rowHighlighted]}>
        <View style={styles.rankContainer}>
          <Text style={[styles.rank, isTopThree && styles.rankTop]}>
            {getMedalEmoji(item.rank)}
          </Text>
        </View>

        <View style={styles.avatarContainer}>
          <Text style={styles.avatarText}>
            {item.display_name[0]?.toUpperCase() || '?'}
          </Text>
        </View>

        <View style={styles.info}>
          <Text style={styles.name}>{item.display_name}</Text>
          <View style={styles.detailsRow}>
            <Text style={styles.tasks}>
              {item.tasks_completed} tasks
            </Text>
            {item.current_streak > 0 && (
              <Text style={styles.streak}>
                🔥 {item.current_streak}
              </Text>
            )}
          </View>
        </View>

        <View style={styles.pointsContainer}>
          <Text style={styles.points}>
            {item.total_points.toLocaleString()}
          </Text>
          <View style={[styles.levelBadge, { backgroundColor: levelColor + '20' }]}>
            <Text style={[styles.levelText, { color: levelColor }]}>
              {level}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={entries}
        renderItem={renderEntry}
        keyExtractor={(item) => item.user_id}
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
            <Text style={styles.emptyEmoji}>🏆</Text>
            <Text style={styles.emptyText}>
              Complete tasks to appear on the leaderboard
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
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  rowHighlighted: {
    borderColor: colors.xpGold + '30',
  },
  rankContainer: {
    width: 36,
    alignItems: 'center',
  },
  rank: {
    ...typography.bodyBold,
    color: colors.textMuted,
  },
  rankTop: {
    fontSize: 20,
  },
  avatarContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary + '30',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  avatarText: {
    ...typography.bodyBold,
    color: colors.primary,
  },
  info: {
    flex: 1,
  },
  name: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  detailsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  tasks: {
    ...typography.small,
    color: colors.textMuted,
  },
  streak: {
    ...typography.small,
    color: colors.streakFire,
  },
  pointsContainer: {
    alignItems: 'flex-end',
  },
  points: {
    ...typography.bodyBold,
    color: colors.xpGold,
  },
  levelBadge: {
    paddingHorizontal: spacing.xs + 2,
    paddingVertical: 1,
    borderRadius: borderRadius.sm,
    marginTop: 2,
  },
  levelText: {
    fontSize: 10,
    fontWeight: '700',
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: spacing.xxl * 2,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, borderRadius, typography } from '../theme';

interface StreakIndicatorProps {
  streak: number;
  longestStreak: number;
}

export function StreakIndicator({ streak, longestStreak }: StreakIndicatorProps) {
  const fireEmoji = streak > 0 ? '🔥' : '❄️';
  const isHot = streak >= 3;

  return (
    <View style={[styles.container, isHot && styles.containerHot]}>
      <Text style={styles.emoji}>{fireEmoji}</Text>
      <View>
        <Text style={styles.streakCount}>{streak} day streak</Text>
        <Text style={styles.bestStreak}>Best: {longestStreak} days</Text>
      </View>
      {isHot && (
        <View style={styles.multiplierBadge}>
          <Text style={styles.multiplierText}>
            {streak >= 7 ? '2x' : '1.5x'}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  containerHot: {
    borderColor: colors.streakFire + '50',
  },
  emoji: {
    fontSize: 28,
  },
  streakCount: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  bestStreak: {
    ...typography.small,
    color: colors.textMuted,
  },
  multiplierBadge: {
    marginLeft: 'auto',
    backgroundColor: colors.streakFire + '30',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  multiplierText: {
    ...typography.bodyBold,
    color: colors.streakFire,
  },
});

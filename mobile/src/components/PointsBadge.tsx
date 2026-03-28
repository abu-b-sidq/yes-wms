import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, borderRadius, typography, getLevelColor } from '../theme';

interface PointsBadgeProps {
  points: number;
  level: string;
  size?: 'small' | 'large';
}

export function PointsBadge({ points, level, size = 'small' }: PointsBadgeProps) {
  const levelColor = getLevelColor(level);
  const isLarge = size === 'large';

  return (
    <View style={[styles.container, isLarge && styles.containerLarge]}>
      <Text style={[styles.points, isLarge && styles.pointsLarge]}>
        {points.toLocaleString()}
      </Text>
      <Text style={[styles.xpLabel, isLarge && styles.xpLabelLarge]}>XP</Text>
      <View style={[styles.levelBadge, { backgroundColor: levelColor + '30' }]}>
        <Text style={[styles.levelText, { color: levelColor }]}>{level}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  containerLarge: {
    gap: spacing.sm,
  },
  points: {
    ...typography.h3,
    color: colors.xpGold,
  },
  pointsLarge: {
    ...typography.h1,
  },
  xpLabel: {
    ...typography.small,
    color: colors.xpGold,
    opacity: 0.7,
  },
  xpLabelLarge: {
    ...typography.body,
  },
  levelBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
    marginLeft: spacing.xs,
  },
  levelText: {
    ...typography.small,
    fontWeight: '700',
  },
});

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, typography } from '../theme';

interface ProgressRingProps {
  current: number;
  total: number;
  size?: number;
  label?: string;
}

export function ProgressRing({
  current,
  total,
  size = 80,
  label,
}: ProgressRingProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <View
        style={[
          styles.ring,
          {
            width: size,
            height: size,
            borderRadius: size / 2,
            borderWidth: size * 0.08,
            borderColor: colors.bgCardLight,
          },
        ]}
      >
        <View
          style={[
            styles.innerRing,
            {
              width: size,
              height: size,
              borderRadius: size / 2,
              borderWidth: size * 0.08,
              borderColor: 'transparent',
              borderTopColor: colors.primary,
              borderRightColor: percentage > 25 ? colors.primary : 'transparent',
              borderBottomColor: percentage > 50 ? colors.primary : 'transparent',
              borderLeftColor: percentage > 75 ? colors.primary : 'transparent',
              transform: [{ rotate: '-45deg' }],
            },
          ]}
        />
      </View>
      <View style={styles.textContainer}>
        <Text style={[styles.percentage, { fontSize: size * 0.25 }]}>
          {percentage}%
        </Text>
        {label && (
          <Text style={[styles.label, { fontSize: size * 0.12 }]}>{label}</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  ring: {
    position: 'absolute',
  },
  innerRing: {
    position: 'absolute',
  },
  textContainer: {
    alignItems: 'center',
  },
  percentage: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  label: {
    ...typography.small,
    color: colors.textMuted,
  },
});

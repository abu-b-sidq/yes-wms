import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, spacing, borderRadius, typography, getStatusColor, shadows } from '../theme';

interface TaskCardProps {
  type: 'pick' | 'drop';
  skuCode: string;
  skuName: string;
  entityCode: string;
  quantity: string;
  status: string;
  batchNumber?: string;
  referenceNumber?: string;
  pointsAwarded?: number;
  onPress?: () => void;
  actionLabel?: string;
  onAction?: () => void;
}

export function TaskCard({
  type,
  skuCode,
  skuName,
  entityCode,
  quantity,
  status,
  batchNumber,
  referenceNumber,
  pointsAwarded,
  onPress,
  actionLabel,
  onAction,
}: TaskCardProps) {
  const statusColor = getStatusColor(status);
  const isPick = type === 'pick';

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.header}>
        <View style={[styles.typeBadge, { backgroundColor: isPick ? colors.primary + '30' : colors.accent + '30' }]}>
          <Text style={[styles.typeText, { color: isPick ? colors.primary : colors.accent }]}>
            {isPick ? '📦 PICK' : '📍 DROP'}
          </Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: statusColor + '20' }]}>
          <Text style={[styles.statusText, { color: statusColor }]}>{status}</Text>
        </View>
      </View>

      <Text style={styles.skuCode}>{skuCode}</Text>
      <Text style={styles.skuName}>{skuName}</Text>

      <View style={styles.details}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>{isPick ? 'From' : 'To'}</Text>
          <Text style={styles.detailValue}>{entityCode}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Qty</Text>
          <Text style={styles.quantityValue}>{quantity}</Text>
        </View>
      </View>

      {batchNumber ? (
        <Text style={styles.batchText}>Batch: {batchNumber}</Text>
      ) : null}

      {referenceNumber ? (
        <Text style={styles.refText}>Ref: {referenceNumber}</Text>
      ) : null}

      {pointsAwarded ? (
        <View style={styles.pointsRow}>
          <Text style={styles.pointsText}>+{pointsAwarded} XP</Text>
        </View>
      ) : null}

      {actionLabel && onAction ? (
        <TouchableOpacity
          style={styles.actionButton}
          onPress={onAction}
          activeOpacity={0.7}
        >
          <Text style={styles.actionText}>{actionLabel}</Text>
        </TouchableOpacity>
      ) : null}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    padding: spacing.md + 2,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.card,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  typeBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  typeText: {
    ...typography.small,
    fontWeight: '700',
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  statusText: {
    ...typography.small,
    fontWeight: '600',
  },
  skuCode: {
    ...typography.h3,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  skuName: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  details: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  detailRow: {
    flex: 1,
  },
  detailLabel: {
    ...typography.small,
    color: colors.textMuted,
  },
  detailValue: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  quantityValue: {
    ...typography.h3,
    color: colors.primary,
  },
  batchText: {
    ...typography.small,
    color: colors.textMuted,
  },
  refText: {
    ...typography.small,
    color: colors.textMuted,
    marginTop: 2,
  },
  pointsRow: {
    marginTop: spacing.sm,
    alignItems: 'flex-end',
  },
  pointsText: {
    ...typography.bodyBold,
    color: colors.xpGold,
  },
  actionButton: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.sm + 2,
    alignItems: 'center',
    marginTop: spacing.md,
    ...shadows.soft,
  },
  actionText: {
    ...typography.bodyBold,
    color: colors.primaryContrast,
  },
});

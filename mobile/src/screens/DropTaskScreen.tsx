import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useTasks } from '../hooks/useTasks';
import { AmbientBackdrop } from '../components/AmbientBackdrop';
import { AnimatedCounter } from '../components/AnimatedCounter';
import { colors, spacing, borderRadius, typography, getStatusColor, shadows } from '../theme';
import {
  triggerLightImpact,
  triggerSuccessNotification,
} from '../utils/haptics';

export function DropTaskScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { startDrop, completeDrop } = useTasks();
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [pointsEarned, setPointsEarned] = useState(0);
  const [txnCompleted, setTxnCompleted] = useState(false);

  const drop = route.params?.drop;
  if (!drop) return null;

  const isAssigned = drop.task_status === 'ASSIGNED';
  const isInProgress = drop.task_status === 'IN_PROGRESS';

  const handleStart = async () => {
    setLoading(true);
    try {
      await startDrop(drop.id);
      await triggerLightImpact();
      drop.task_status = 'IN_PROGRESS';
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const result = await completeDrop(drop.id);
      await triggerSuccessNotification();
      setCompleted(true);
      setPointsEarned(result.drop.points_awarded);
      setTxnCompleted(result.transaction_completed);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  if (completed) {
    return (
      <View style={styles.screen}>
        <AmbientBackdrop variant="task" />
        <View style={styles.successContainer}>
          {txnCompleted ? (
            <>
              <Text style={styles.successEmoji}>🏆</Text>
              <Text style={styles.successTitle}>Transaction Complete!</Text>
              <Text style={styles.successSubtitle}>
                All picks and drops finished
              </Text>
            </>
          ) : (
            <>
              <Text style={styles.successEmoji}>📍</Text>
              <Text style={styles.successTitle}>Drop Complete!</Text>
            </>
          )}
          <View style={styles.pointsContainer}>
            <AnimatedCounter
              value={pointsEarned}
              prefix="+"
              suffix=" XP"
              style={styles.pointsValue}
            />
          </View>
          <TouchableOpacity
            style={styles.doneButton}
            onPress={() => navigation.popToTop()}
          >
            <Text style={styles.doneButtonText}>Back to Dashboard</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <AmbientBackdrop variant="task" />
      <View style={styles.container}>
        <View style={styles.card}>
        <View style={styles.statusRow}>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getStatusColor(drop.task_status) + '20' },
            ]}
          >
            <Text
              style={[
                styles.statusText,
                { color: getStatusColor(drop.task_status) },
              ]}
            >
              {drop.task_status}
            </Text>
          </View>
          <Text style={styles.taskType}>📍 DROP</Text>
        </View>

        <Text style={styles.skuCode}>{drop.sku_code}</Text>
        <Text style={styles.skuName}>{drop.sku_name}</Text>

        <View style={styles.infoGrid}>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Destination</Text>
            <Text style={styles.infoValue}>{drop.dest_entity_code}</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Type</Text>
            <Text style={styles.infoValue}>{drop.dest_entity_type}</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Quantity</Text>
            <Text style={styles.quantityValue}>{drop.quantity}</Text>
          </View>
          {drop.batch_number ? (
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Batch</Text>
              <Text style={styles.infoValue}>{drop.batch_number}</Text>
            </View>
          ) : null}
        </View>

        {drop.reference_number ? (
          <Text style={styles.refText}>Ref: {drop.reference_number}</Text>
        ) : null}
        </View>

        <View style={styles.actions}>
          {isAssigned ? (
            <TouchableOpacity
              style={styles.startButton}
              onPress={handleStart}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color={colors.primaryContrast} />
              ) : (
                <>
                  <Text style={styles.actionEmoji}>▶️</Text>
                  <Text style={styles.actionText}>Start Drop</Text>
                </>
              )}
            </TouchableOpacity>
          ) : null}

          {isInProgress ? (
            <TouchableOpacity
              style={styles.completeButton}
              onPress={handleComplete}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color={colors.primaryContrast} />
              ) : (
                <>
                  <Text style={styles.actionEmoji}>✅</Text>
                  <Text style={styles.actionText}>Confirm Drop Complete</Text>
                </>
              )}
            </TouchableOpacity>
          ) : null}
        </View>
      </View>
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
    padding: spacing.md,
  },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.card,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  statusText: {
    ...typography.small,
    fontWeight: '600',
  },
  taskType: {
    ...typography.bodyBold,
    color: colors.accent,
  },
  skuCode: {
    ...typography.h1,
    color: colors.textPrimary,
  },
  skuName: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  infoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  infoItem: {
    width: '45%',
    marginBottom: spacing.sm,
  },
  infoLabel: {
    ...typography.small,
    color: colors.textMuted,
    marginBottom: 2,
  },
  infoValue: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  quantityValue: {
    ...typography.h2,
    color: colors.accent,
  },
  refText: {
    ...typography.caption,
    color: colors.textMuted,
    marginTop: spacing.sm,
  },
  actions: {
    marginTop: 'auto',
    paddingBottom: spacing.xl,
  },
  startButton: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.lg,
    padding: spacing.md + 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    ...shadows.soft,
  },
  completeButton: {
    backgroundColor: colors.accent,
    borderRadius: borderRadius.lg,
    padding: spacing.md + 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    ...shadows.soft,
  },
  actionEmoji: {
    fontSize: 20,
  },
  actionText: {
    ...typography.bodyBold,
    color: colors.primaryContrast,
    fontSize: 18,
  },
  successContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
    margin: spacing.md,
    backgroundColor: colors.glass,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.card,
  },
  successEmoji: {
    fontSize: 64,
    marginBottom: spacing.md,
  },
  successTitle: {
    ...typography.h1,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  successSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  pointsContainer: {
    marginBottom: spacing.xl,
  },
  pointsValue: {
    fontSize: 48,
    fontWeight: '800',
    color: colors.xpGold,
  },
  doneButton: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    ...shadows.soft,
  },
  doneButtonText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
});

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useTasks } from '../hooks/useTasks';
import { AnimatedCounter } from '../components/AnimatedCounter';
import { colors, spacing, borderRadius, typography, getStatusColor } from '../theme';

export function PickTaskScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { startPick, completePick } = useTasks();
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [pointsEarned, setPointsEarned] = useState(0);
  const [assignedDrop, setAssignedDrop] = useState<any>(null);

  const pick = route.params?.pick;
  if (!pick) return null;

  const isAssigned = pick.task_status === 'ASSIGNED';
  const isInProgress = pick.task_status === 'IN_PROGRESS';

  const handleStart = async () => {
    setLoading(true);
    try {
      await startPick(pick.id);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      pick.task_status = 'IN_PROGRESS';
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const result = await completePick(pick.id);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setCompleted(true);
      setPointsEarned(result.pick.points_awarded);
      if (result.drop) {
        setAssignedDrop(result.drop);
      }
    } catch (err: any) {
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoToDrop = () => {
    if (assignedDrop) {
      navigation.replace('DropTask', { drop: assignedDrop });
    }
  };

  if (completed) {
    return (
      <View style={styles.successContainer}>
        <Text style={styles.successEmoji}>🎉</Text>
        <Text style={styles.successTitle}>Pick Complete!</Text>
        <View style={styles.pointsContainer}>
          <AnimatedCounter
            value={pointsEarned}
            prefix="+"
            suffix=" XP"
            style={styles.pointsValue}
          />
        </View>
        {assignedDrop ? (
          <TouchableOpacity style={styles.nextButton} onPress={handleGoToDrop}>
            <Text style={styles.nextButtonText}>Go to Drop Task →</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={styles.doneButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.doneButtonText}>Back to Dashboard</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <View style={styles.statusRow}>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getStatusColor(pick.task_status) + '20' },
            ]}
          >
            <Text
              style={[
                styles.statusText,
                { color: getStatusColor(pick.task_status) },
              ]}
            >
              {pick.task_status}
            </Text>
          </View>
          <Text style={styles.taskType}>📦 PICK</Text>
        </View>

        <Text style={styles.skuCode}>{pick.sku_code}</Text>
        <Text style={styles.skuName}>{pick.sku_name}</Text>

        <View style={styles.infoGrid}>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Source Location</Text>
            <Text style={styles.infoValue}>{pick.source_entity_code}</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Type</Text>
            <Text style={styles.infoValue}>{pick.source_entity_type}</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Quantity</Text>
            <Text style={styles.quantityValue}>{pick.quantity}</Text>
          </View>
          {pick.batch_number ? (
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Batch</Text>
              <Text style={styles.infoValue}>{pick.batch_number}</Text>
            </View>
          ) : null}
        </View>

        {pick.reference_number ? (
          <Text style={styles.refText}>Ref: {pick.reference_number}</Text>
        ) : null}
      </View>

      <View style={styles.actions}>
        {isAssigned && (
          <TouchableOpacity
            style={styles.startButton}
            onPress={handleStart}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color={colors.textPrimary} />
            ) : (
              <>
                <Text style={styles.actionEmoji}>▶️</Text>
                <Text style={styles.actionText}>Start Pick</Text>
              </>
            )}
          </TouchableOpacity>
        )}

        {isInProgress && (
          <TouchableOpacity
            style={styles.completeButton}
            onPress={handleComplete}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color={colors.textPrimary} />
            ) : (
              <>
                <Text style={styles.actionEmoji}>✅</Text>
                <Text style={styles.actionText}>Confirm Pick Complete</Text>
              </>
            )}
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
    padding: spacing.md,
  },
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
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
    color: colors.primary,
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
    color: colors.primary,
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
  },
  completeButton: {
    backgroundColor: colors.success,
    borderRadius: borderRadius.lg,
    padding: spacing.md + 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  actionEmoji: {
    fontSize: 20,
  },
  actionText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    fontSize: 18,
  },
  // Success state
  successContainer: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  successEmoji: {
    fontSize: 64,
    marginBottom: spacing.md,
  },
  successTitle: {
    ...typography.h1,
    color: colors.textPrimary,
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
  nextButton: {
    backgroundColor: colors.accent,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
  },
  nextButtonText: {
    ...typography.bodyBold,
    color: colors.bg,
    fontSize: 18,
  },
  doneButton: {
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: colors.bgCardLight,
  },
  doneButtonText: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
});

import React from 'react';
import { StyleSheet, View } from 'react-native';
import { colors } from '../theme';

type AmbientVariant = 'default' | 'auth' | 'task';

interface AmbientBackdropProps {
  variant?: AmbientVariant;
}

export function AmbientBackdrop({ variant = 'default' }: AmbientBackdropProps) {
  return (
    <View pointerEvents="none" style={styles.container}>
      <View style={[styles.orb, styles.orbTopRight, variant === 'auth' && styles.orbTopRightAuth]} />
      <View style={[styles.orb, styles.orbTopLeft, variant === 'task' && styles.orbTopLeftTask]} />
      <View style={[styles.orb, styles.orbBottomLeft, variant === 'auth' && styles.orbBottomLeftAuth]} />
      <View style={[styles.frame, styles.framePrimary, variant === 'auth' && styles.framePrimaryAuth]} />
      <View style={[styles.frame, styles.frameSecondary, variant === 'task' && styles.frameSecondaryTask]} />
      <View style={[styles.wire, styles.wireOne]} />
      <View style={[styles.wire, styles.wireTwo]} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    overflow: 'hidden',
  },
  orb: {
    position: 'absolute',
    borderRadius: 999,
  },
  orbTopRight: {
    top: -60,
    right: -40,
    width: 240,
    height: 240,
    backgroundColor: colors.primary + '1F',
  },
  orbTopRightAuth: {
    top: -20,
    right: -10,
    width: 280,
    height: 280,
    backgroundColor: colors.secondary + '26',
  },
  orbTopLeft: {
    top: 48,
    left: -88,
    width: 220,
    height: 220,
    backgroundColor: colors.secondary + '14',
  },
  orbTopLeftTask: {
    top: -36,
    left: -64,
    width: 200,
    height: 200,
    backgroundColor: colors.accent + '14',
  },
  orbBottomLeft: {
    bottom: -110,
    left: -70,
    width: 250,
    height: 250,
    backgroundColor: colors.accent + '14',
  },
  orbBottomLeftAuth: {
    bottom: -80,
    left: -40,
    width: 280,
    height: 280,
    backgroundColor: colors.primaryLight + '16',
  },
  frame: {
    position: 'absolute',
    borderWidth: 1,
    borderColor: colors.bgCardLight,
    backgroundColor: colors.glassSoft,
  },
  framePrimary: {
    top: 112,
    right: 18,
    width: 180,
    height: 116,
    borderRadius: 26,
    transform: [{ rotate: '10deg' }],
  },
  framePrimaryAuth: {
    top: 68,
    right: 12,
    width: 220,
    height: 144,
    borderColor: colors.primary + '40',
  },
  frameSecondary: {
    bottom: 156,
    left: 16,
    width: 136,
    height: 82,
    borderRadius: 22,
    transform: [{ rotate: '-12deg' }],
  },
  frameSecondaryTask: {
    bottom: 96,
    left: 22,
    width: 160,
    height: 92,
  },
  wire: {
    position: 'absolute',
    height: 2,
    borderRadius: 999,
  },
  wireOne: {
    top: 168,
    left: 68,
    width: 156,
    backgroundColor: colors.primary + '40',
    transform: [{ rotate: '-14deg' }],
  },
  wireTwo: {
    bottom: 204,
    right: 64,
    width: 120,
    backgroundColor: colors.accent + '34',
    transform: [{ rotate: '18deg' }],
  },
});

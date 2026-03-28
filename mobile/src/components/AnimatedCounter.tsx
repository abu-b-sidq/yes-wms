import React, { useEffect, useRef } from 'react';
import { Text, Animated, StyleSheet, TextStyle } from 'react-native';
import { colors, typography } from '../theme';

interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  suffix?: string;
  style?: TextStyle;
  duration?: number;
}

export function AnimatedCounter({
  value,
  prefix = '',
  suffix = '',
  style,
  duration = 800,
}: AnimatedCounterProps) {
  const animValue = useRef(new Animated.Value(0)).current;
  const displayValue = useRef(0);
  const textRef = useRef<Text>(null);

  useEffect(() => {
    animValue.setValue(0);
    Animated.timing(animValue, {
      toValue: value,
      duration,
      useNativeDriver: false,
    }).start();

    const listener = animValue.addListener(({ value: v }) => {
      displayValue.current = Math.round(v);
    });

    return () => {
      animValue.removeListener(listener);
    };
  }, [value, duration, animValue]);

  return (
    <Text ref={textRef} style={[styles.text, style]}>
      {prefix}{value.toLocaleString()}{suffix}
    </Text>
  );
}

const styles = StyleSheet.create({
  text: {
    ...typography.h2,
    color: colors.xpGold,
  },
});

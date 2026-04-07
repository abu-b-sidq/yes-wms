import React from 'react';
import { ActivityIndicator, View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuth } from '../auth/AuthContext';
import { LoginScreen } from '../screens/LoginScreen';
import { FacilityPickerScreen } from '../screens/FacilityPickerScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { AvailableTasksScreen } from '../screens/AvailableTasksScreen';
import { PickTaskScreen } from '../screens/PickTaskScreen';
import { DropTaskScreen } from '../screens/DropTaskScreen';
import { MyTasksScreen } from '../screens/MyTasksScreen';
import { LeaderboardScreen } from '../screens/LeaderboardScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { colors, typography, borderRadius, shadows } from '../theme';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const tabScreenOptions = {
  headerStyle: { backgroundColor: colors.bgSurface },
  headerTintColor: colors.textPrimary,
  headerTitleStyle: {
    ...typography.bodyBold,
  },
  headerShadowVisible: false,
  tabBarStyle: {
    position: 'absolute' as const,
    left: 16,
    right: 16,
    bottom: 18,
    height: 78,
    paddingBottom: 14,
    paddingTop: 10,
    backgroundColor: colors.bgSurface,
    borderTopColor: colors.bgCardLight,
    borderColor: colors.bgCardLight,
    borderTopWidth: 1,
    borderWidth: 1,
    borderRadius: borderRadius.xl,
    ...shadows.card,
  },
  tabBarActiveTintColor: colors.primary,
  tabBarInactiveTintColor: colors.textMuted,
  tabBarLabelStyle: {
    ...typography.small,
    marginTop: 2,
    fontWeight: '700' as const,
  },
  tabBarItemStyle: {
    paddingTop: 4,
  },
};

function MainTabs() {
  return (
    <Tab.Navigator screenOptions={tabScreenOptions}>
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          headerShown: false,
          tabBarIcon: ({ color, focused }) => (
            <TabIcon emoji="🏠" color={color} focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="AvailableTasks"
        component={AvailableTasksScreen}
        options={{
          title: 'Available',
          headerTitle: 'Available Tasks',
          tabBarIcon: ({ color, focused }) => (
            <TabIcon emoji="📋" color={color} focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="MyTasks"
        component={MyTasksScreen}
        options={{
          title: 'My Tasks',
          headerTitle: 'My Tasks',
          tabBarIcon: ({ color, focused }) => (
            <TabIcon emoji="📦" color={color} focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="Leaderboard"
        component={LeaderboardScreen}
        options={{
          title: 'Ranks',
          headerTitle: 'Leaderboard',
          tabBarIcon: ({ color, focused }) => (
            <TabIcon emoji="🏆" color={color} focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          headerShown: false,
          tabBarIcon: ({ color, focused }) => (
            <TabIcon emoji="👤" color={color} focused={focused} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

function TabIcon({
  emoji,
  color,
  focused,
}: {
  emoji: string;
  color: string;
  focused: boolean;
}) {
  return (
    <View
      style={[
        tabIconStyles.container,
        focused && tabIconStyles.containerFocused,
      ]}
    >
      <Text style={[tabIconStyles.emoji, { opacity: focused ? 1 : 0.58 }]}>
        {emoji}
      </Text>
    </View>
  );
}

export function AppNavigator() {
  const { user, loading, selectedFacility } = useAuth();

  if (loading) {
    return (
      <View style={loadingStyles.container}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer
      theme={{
        dark: true,
        colors: {
          primary: colors.primary,
          background: colors.bg,
          card: colors.bgSurface,
          text: colors.textPrimary,
          border: colors.bgCardLight,
          notification: colors.secondary,
        },
        fonts: {
          regular: { fontFamily: 'System', fontWeight: '400' },
          medium: { fontFamily: 'System', fontWeight: '500' },
          bold: { fontFamily: 'System', fontWeight: '700' },
          heavy: { fontFamily: 'System', fontWeight: '800' },
        },
      }}
    >
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: colors.bgSurface },
          headerTintColor: colors.textPrimary,
          headerTitleStyle: {
            ...typography.bodyBold,
          },
          headerShadowVisible: false,
          contentStyle: {
            backgroundColor: colors.bg,
          },
        }}
      >
        {!user ? (
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            options={{ headerShown: false }}
          />
        ) : !selectedFacility ? (
          <Stack.Screen
            name="FacilityPicker"
            component={FacilityPickerScreen}
            options={{ headerShown: false }}
          />
        ) : (
          <>
            <Stack.Screen
              name="Main"
              component={MainTabs}
              options={{ headerShown: false }}
            />
            <Stack.Screen
              name="PickTask"
              component={PickTaskScreen}
              options={{ title: 'Pick Task' }}
            />
            <Stack.Screen
              name="DropTask"
              component={DropTaskScreen}
              options={{ title: 'Drop Task' }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const loadingStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

const tabIconStyles = StyleSheet.create({
  container: {
    width: 42,
    height: 32,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  containerFocused: {
    backgroundColor: colors.primary + '20',
    borderWidth: 1,
    borderColor: colors.primary + '2E',
  },
  emoji: {
    fontSize: 20,
  },
});

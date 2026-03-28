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
import { colors, typography } from '../theme';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const tabScreenOptions = {
  headerStyle: { backgroundColor: colors.bgCard },
  headerTintColor: colors.textPrimary,
  tabBarStyle: {
    backgroundColor: colors.bgCard,
    borderTopColor: colors.bgCardLight,
    borderTopWidth: 1,
    height: 85,
    paddingBottom: 20,
    paddingTop: 8,
  },
  tabBarActiveTintColor: colors.primary,
  tabBarInactiveTintColor: colors.textMuted,
  tabBarLabelStyle: {
    ...typography.small,
    marginTop: 2,
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
          tabBarIcon: ({ color }) => (
            <TabIcon emoji="🏠" color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="AvailableTasks"
        component={AvailableTasksScreen}
        options={{
          title: 'Available',
          headerTitle: 'Available Tasks',
          tabBarIcon: ({ color }) => (
            <TabIcon emoji="📋" color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="MyTasks"
        component={MyTasksScreen}
        options={{
          title: 'My Tasks',
          headerTitle: 'My Tasks',
          tabBarIcon: ({ color }) => (
            <TabIcon emoji="📦" color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Leaderboard"
        component={LeaderboardScreen}
        options={{
          title: 'Ranks',
          headerTitle: 'Leaderboard',
          tabBarIcon: ({ color }) => (
            <TabIcon emoji="🏆" color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          headerShown: false,
          tabBarIcon: ({ color }) => (
            <TabIcon emoji="👤" color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

function TabIcon({ emoji, color }: { emoji: string; color: string }) {
  return (
    <View style={{ opacity: color === colors.primary ? 1 : 0.5 }}>
      <Text style={{ fontSize: 22 }}>{emoji}</Text>
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
          card: colors.bgCard,
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
          headerStyle: { backgroundColor: colors.bgCard },
          headerTintColor: colors.textPrimary,
          headerBackTitleVisible: false,
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

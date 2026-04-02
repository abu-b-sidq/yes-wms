import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  // Public routes
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
    canActivate: [guestGuard]
  },
  {
    path: 'facility-select',
    loadComponent: () => import('./pages/facility-select/facility-select.component').then(m => m.FacilitySelectComponent),
    canActivate: [authGuard]
  },

  // Protected routes (inside shell layout)
  {
    path: '',
    loadComponent: () => import('./layout/shell/shell.component').then(m => m.ShellComponent),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
        data: { title: 'Dashboard' }
      },

      // Masters
      {
        path: 'masters/sku',
        loadComponent: () => import('./pages/masters/sku/sku.component').then(m => m.SkuComponent),
        data: { title: 'SKUs' }
      },
      {
        path: 'masters/zone',
        loadComponent: () => import('./pages/masters/zone/zone.component').then(m => m.ZoneComponent),
        data: { title: 'Zones' }
      },
      {
        path: 'masters/location',
        loadComponent: () => import('./pages/masters/location/location.component').then(m => m.LocationComponent),
        data: { title: 'Locations' }
      },

      // Transactions
      {
        path: 'transactions',
        loadComponent: () => import('./pages/transactions/transactions-list/transactions-list.component').then(m => m.TransactionsListComponent),
        data: { title: 'Transactions' }
      },
      {
        path: 'transactions/grn',
        loadComponent: () => import('./pages/transactions/grn/grn.component').then(m => m.GrnComponent),
        data: { title: 'GRN' }
      },
      {
        path: 'transactions/move',
        loadComponent: () => import('./pages/transactions/move/move.component').then(m => m.MoveComponent),
        data: { title: 'Move' }
      },
      {
        path: 'transactions/putaway',
        loadComponent: () => import('./pages/transactions/putaway/putaway.component').then(m => m.PutawayComponent),
        data: { title: 'Putaway' }
      },
      {
        path: 'transactions/order-pick',
        loadComponent: () => import('./pages/transactions/order-pick/order-pick.component').then(m => m.OrderPickComponent),
        data: { title: 'Order Pick' }
      },

      // Inventory
      {
        path: 'inventory',
        loadComponent: () => import('./pages/inventory/inventory.component').then(m => m.InventoryComponent),
        data: { title: 'Inventory' }
      },

      // Integrations / Connectors
      {
        path: 'connectors',
        loadComponent: () => import('./pages/connectors/connectors.component').then(m => m.ConnectorsComponent),
        data: { title: 'Integrations' }
      },
      {
        path: 'connectors/:id/logs',
        loadComponent: () => import('./pages/connectors/connector-logs/connector-logs.component').then(m => m.ConnectorLogsComponent),
        data: { title: 'Sync Logs' }
      }
    ]
  },

  { path: '**', redirectTo: 'dashboard' }
];

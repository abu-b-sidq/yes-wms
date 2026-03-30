import { Component, Input, Output, EventEmitter, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from '../../core/auth/auth.service';

export interface NavItem {
  label: string;
  icon: string;
  route?: string;
  children?: NavItem[];
  permission?: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    CommonModule, RouterModule,
    MatListModule, MatIconModule, MatExpansionModule,
    MatDividerModule, MatTooltipModule
  ],
  template: `
    <aside class="sidebar" [class.collapsed]="collapsed">
      <!-- Logo -->
      <div class="sidebar-logo">
        <div class="logo-icon">
          <mat-icon>warehouse</mat-icon>
        </div>
        <span class="logo-text" *ngIf="!collapsed">YES WMS</span>
      </div>

      <mat-divider></mat-divider>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <!-- Dashboard -->
        <a mat-list-item routerLink="/dashboard" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Dashboard' : ''" matTooltipPosition="right"
           class="nav-item">
          <mat-icon matListItemIcon>dashboard</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Dashboard</span>
        </a>

        <!-- Masters -->
        <div class="nav-section" *ngIf="!collapsed">
          <span class="nav-section-label">Masters</span>
        </div>
        <mat-divider *ngIf="collapsed"></mat-divider>

        <a mat-list-item routerLink="/masters/sku" routerLinkActive="active"
           [matTooltip]="collapsed ? 'SKUs' : ''" matTooltipPosition="right"
           class="nav-item">
          <mat-icon matListItemIcon>inventory_2</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">SKUs</span>
        </a>

        <a mat-list-item routerLink="/masters/zone" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Zones' : ''" matTooltipPosition="right"
           class="nav-item">
          <mat-icon matListItemIcon>grid_view</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Zones</span>
        </a>

        <a mat-list-item routerLink="/masters/location" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Locations' : ''" matTooltipPosition="right"
           class="nav-item">
          <mat-icon matListItemIcon>location_on</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Locations</span>
        </a>

        <!-- Transactions -->
        <div class="nav-section" *ngIf="!collapsed">
          <span class="nav-section-label">Transactions</span>
        </div>
        <mat-divider *ngIf="collapsed"></mat-divider>

        <a mat-list-item routerLink="/transactions" routerLinkActive="active"
           [matTooltip]="collapsed ? 'All Transactions' : ''" matTooltipPosition="right"
           class="nav-item">
          <mat-icon matListItemIcon>receipt_long</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">All Transactions</span>
        </a>

        <a mat-list-item routerLink="/transactions/grn" routerLinkActive="active"
           [matTooltip]="collapsed ? 'GRN' : ''" matTooltipPosition="right"
           class="nav-item nav-item-sub">
          <mat-icon matListItemIcon>input</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">GRN - Receive</span>
        </a>

        <a mat-list-item routerLink="/transactions/move" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Move' : ''" matTooltipPosition="right"
           class="nav-item nav-item-sub">
          <mat-icon matListItemIcon>swap_horiz</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Move</span>
        </a>

        <a mat-list-item routerLink="/transactions/putaway" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Putaway' : ''" matTooltipPosition="right"
           class="nav-item nav-item-sub">
          <mat-icon matListItemIcon>move_to_inbox</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Putaway</span>
        </a>

        <a mat-list-item routerLink="/transactions/order-pick" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Order Pick' : ''" matTooltipPosition="right"
           class="nav-item nav-item-sub">
          <mat-icon matListItemIcon>shopping_cart</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Order Pick</span>
        </a>

        <!-- Inventory -->
        <div class="nav-section" *ngIf="!collapsed">
          <span class="nav-section-label">Inventory</span>
        </div>
        <mat-divider *ngIf="collapsed"></mat-divider>

        <a mat-list-item routerLink="/inventory" routerLinkActive="active"
           [matTooltip]="collapsed ? 'Inventory' : ''" matTooltipPosition="right"
           class="nav-item">
          <mat-icon matListItemIcon>inventory</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Stock Balances</span>
        </a>
      </nav>

      <!-- Bottom actions -->
      <div class="sidebar-bottom">
        <mat-divider></mat-divider>
        <a mat-list-item class="nav-item" (click)="onLogout()"
           [matTooltip]="collapsed ? 'Logout' : ''" matTooltipPosition="right">
          <mat-icon matListItemIcon>logout</mat-icon>
          <span matListItemTitle *ngIf="!collapsed">Logout</span>
        </a>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      display: flex;
      flex-direction: column;
      height: 100%;
      width: 240px;
      background: #1e293b;
      color: #e2e8f0;
      transition: width 0.3s ease;
      overflow: hidden;
    }
    .sidebar.collapsed {
      width: 60px;
    }
    .sidebar-logo {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      height: 64px;
      flex-shrink: 0;
    }
    .logo-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: #3b82f6;
      border-radius: 8px;
      flex-shrink: 0;
    }
    .logo-icon mat-icon {
      color: white;
      font-size: 20px;
      width: 20px;
      height: 20px;
    }
    .logo-text {
      font-weight: 700;
      font-size: 16px;
      color: white;
      white-space: nowrap;
    }
    .sidebar-nav {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 8px 0;
    }
    .nav-section {
      padding: 8px 16px 4px;
    }
    .nav-section-label {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #64748b;
    }
    .nav-item {
      color: #94a3b8 !important;
      border-radius: 6px !important;
      margin: 2px 8px !important;
      transition: all 0.15s ease;
      cursor: pointer;
    }
    .nav-item:hover {
      background: rgba(59, 130, 246, 0.15) !important;
      color: #e2e8f0 !important;
    }
    .nav-item.active {
      background: rgba(59, 130, 246, 0.25) !important;
      color: #60a5fa !important;
    }
    .nav-item mat-icon {
      color: inherit !important;
    }
    .nav-item-sub {
      padding-left: 24px !important;
    }
    .sidebar-bottom {
      flex-shrink: 0;
      padding: 8px 0;
    }
    mat-divider {
      border-color: #334155 !important;
      margin: 4px 0;
    }
  `]
})
export class SidebarComponent {
  @Input() collapsed = false;
  @Output() toggleCollapse = new EventEmitter<void>();

  private auth = inject(AuthService);

  onLogout(): void {
    this.auth.logout();
  }
}

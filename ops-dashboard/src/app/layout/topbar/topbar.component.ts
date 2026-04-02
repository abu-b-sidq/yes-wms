import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [
    CommonModule, MatToolbarModule, MatIconModule, MatButtonModule,
    MatMenuModule, MatDividerModule, MatChipsModule
  ],
  template: `
    <mat-toolbar class="topbar" color="primary">
      <!-- Hamburger -->
      <button mat-icon-button (click)="onToggleSidebar()" class="hamburger-btn">
        <mat-icon>{{ sidebarCollapsed ? 'menu' : 'menu_open' }}</mat-icon>
      </button>

      <!-- Page title -->
      <span class="page-title">{{ title }}</span>

      <span class="spacer"></span>

      <!-- Facility badge -->
      <div class="facility-badge" *ngIf="currentFacility">
        <mat-icon class="facility-icon">warehouse</mat-icon>
        <span class="facility-name">{{ currentFacility.name }}</span>
        <button mat-icon-button class="switch-btn"
                [matMenuTriggerFor]="facilityMenu"
                matTooltip="Switch Facility">
          <mat-icon>expand_more</mat-icon>
        </button>
        <mat-menu #facilityMenu="matMenu">
          <div class="menu-header">Switch Facility</div>
          <mat-divider></mat-divider>
          <button mat-menu-item
                  *ngFor="let facility of availableFacilities"
                  (click)="onSwitchFacility(facility)"
                  [class.active-facility]="facility.id === currentFacility.id">
            <mat-icon>{{ facility.id === currentFacility.id ? 'check' : 'warehouse' }}</mat-icon>
            <span>{{ facility.name }}</span>
          </button>
        </mat-menu>
      </div>

      <!-- User menu -->
      <button mat-icon-button [matMenuTriggerFor]="userMenu" class="user-btn">
        <div class="user-avatar">
          {{ userInitials }}
        </div>
      </button>
      <mat-menu #userMenu="matMenu">
        <div class="user-menu-header">
          <div class="user-avatar-large">{{ userInitials }}</div>
          <div class="user-info">
            <div class="user-name">{{ userName }}</div>
            <div class="user-email">{{ userEmail }}</div>
          </div>
        </div>
        <mat-divider></mat-divider>
        <button mat-menu-item (click)="onLogout()">
          <mat-icon>logout</mat-icon>
          <span>Logout</span>
        </button>
      </mat-menu>
    </mat-toolbar>
  `,
  styles: [`
    .topbar {
      position: sticky;
      top: 0;
      background: rgba(20, 25, 30, 0.72) !important;
      color: var(--ops-text) !important;
      box-shadow: none;
      border-bottom: 1px solid var(--ops-border);
      backdrop-filter: blur(24px);
      z-index: 10;
      height: 72px;
      padding: 0 14px 0 20px;
    }
    .hamburger-btn {
      color: var(--ops-text-muted);
      margin-right: 10px;
      background: rgba(255, 255, 255, 0.04);
      border-radius: 12px;
    }
    .page-title {
      font-size: 19px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--ops-text);
    }
    .spacer { flex: 1; }
    .facility-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--ops-border);
      border-radius: 16px;
      padding: 5px 8px 5px 12px;
      margin-right: 10px;
      cursor: pointer;
    }
    .facility-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: var(--ops-primary);
    }
    .facility-name {
      font-size: 13px;
      font-weight: 600;
      color: var(--ops-text);
      max-width: 150px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .switch-btn {
      width: 28px;
      height: 28px;
      line-height: 28px;
      color: var(--ops-text-muted);
    }
    .switch-btn mat-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
    }
    .user-btn {
      margin-left: 4px;
    }
    .user-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: linear-gradient(180deg, rgba(75, 152, 235, 0.9) 0%, rgba(67, 136, 211, 0.9) 100%);
      color: #151821;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 12px;
      box-shadow: 0 8px 18px rgba(75, 152, 235, 0.18);
    }
    .user-avatar-large {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(180deg, rgba(75, 152, 235, 0.9) 0%, rgba(67, 136, 211, 0.9) 100%);
      color: #151821;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
    }
    .user-menu-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
    }
    .user-info {
      flex: 1;
    }
    .user-name {
      font-weight: 600;
      font-size: 14px;
      color: var(--ops-text);
    }
    .user-email {
      font-size: 12px;
      color: var(--ops-text-muted);
    }
    .menu-header {
      padding: 8px 16px;
      font-size: 12px;
      font-weight: 600;
      color: var(--ops-text-soft);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .active-facility {
      background: var(--ops-primary-soft);
      color: var(--ops-primary);
    }

    @media (max-width: 600px) {
      .facility-name {
        display: none;
      }
    }
  `]
})
export class TopbarComponent {
  @Input() sidebarCollapsed = false;
  @Input() title = 'OPS Dashboard';
  @Output() toggleSidebar = new EventEmitter<void>();

  private auth = inject(AuthService);
  private router = inject(Router);

  get currentFacility() { return this.auth.currentFacility(); }
  get availableFacilities() { return this.auth.availableFacilities(); }
  get userName() { return this.auth.currentUser()?.display_name ?? ''; }
  get userEmail() { return this.auth.currentUser()?.email ?? ''; }
  get userInitials() {
    const name = this.userName;
    if (!name) return '?';
    const parts = name.trim().split(' ');
    return (parts[0][0] + (parts[1]?.[0] ?? '')).toUpperCase();
  }

  onToggleSidebar(): void {
    this.toggleSidebar.emit();
  }

  onSwitchFacility(facility: typeof this.currentFacility): void {
    if (facility) {
      this.auth.selectFacility(facility);
    }
  }

  onLogout(): void {
    this.auth.logout();
  }
}

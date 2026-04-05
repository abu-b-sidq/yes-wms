import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from '../../core/auth/auth.service';
import { Facility } from '../../core/models/user.model';
import { ThemePreference, ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-facility-select',
  standalone: true,
  imports: [
    CommonModule, MatCardModule, MatButtonModule,
    MatIconModule, MatProgressSpinnerModule, MatDividerModule,
    MatMenuModule, MatTooltipModule
  ],
  template: `
    <div class="facility-select-page" data-scene="facility-select">
      <button mat-icon-button class="theme-fab"
              [matMenuTriggerFor]="themeMenu"
              aria-label="Theme menu"
              [matTooltip]="themeTooltip">
        <mat-icon>{{ themeIcon }}</mat-icon>
      </button>

      <mat-menu #themeMenu="matMenu">
        <div class="menu-header">Theme</div>
        <mat-divider></mat-divider>
        <button mat-menu-item (click)="setTheme('system')" [class.active-theme]="theme.preference() === 'system'">
          <mat-icon>brightness_auto</mat-icon>
          <span>System</span>
        </button>
        <button mat-menu-item (click)="setTheme('light')" [class.active-theme]="theme.preference() === 'light'">
          <mat-icon>light_mode</mat-icon>
          <span>Light</span>
        </button>
        <button mat-menu-item (click)="setTheme('dark')" [class.active-theme]="theme.preference() === 'dark'">
          <mat-icon>dark_mode</mat-icon>
          <span>Dark</span>
        </button>
      </mat-menu>

      <div class="facility-card">
        <!-- Header -->
        <div class="card-header">
          <div class="logo-circle">
            <mat-icon>warehouse</mat-icon>
          </div>
          <h2>Select Facility</h2>
          <p>Choose a warehouse to continue</p>
        </div>

        <mat-divider></mat-divider>

        <!-- User info -->
        <div class="user-info">
          <div class="user-avatar">{{ userInitials }}</div>
          <div>
            <div class="user-name">{{ userName }}</div>
            <div class="user-email">{{ userEmail }}</div>
          </div>
        </div>

        <mat-divider></mat-divider>

        <!-- Facilities list -->
        <div class="facilities-list">
          <div class="list-label">Available Facilities</div>

          <div class="empty-facilities" *ngIf="facilities.length === 0">
            <mat-icon>info_outline</mat-icon>
            <p>No facilities assigned. Contact your administrator.</p>
          </div>

          <button class="facility-item"
                  *ngFor="let facility of facilities"
                  [disabled]="loading()"
                  (click)="selectFacility(facility)">
            <div class="facility-icon">
              <mat-icon>warehouse</mat-icon>
            </div>
            <div class="facility-info">
              <span class="facility-name">{{ facility.name }}</span>
              <span class="facility-code">{{ facility.code }}</span>
            </div>
            <mat-icon class="chevron">chevron_right</mat-icon>
          </button>
        </div>

        <mat-divider></mat-divider>

        <button mat-stroked-button class="logout-btn" (click)="onLogout()">
          <mat-icon>logout</mat-icon>
          Sign Out
        </button>
      </div>
    </div>
  `,
  styles: [`
    .facility-select-page {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--ops-auth-bg, var(--ops-page-bg));
      padding: 16px;
      position: relative;
      overflow: hidden;
    }
    .facility-select-page::before,
    .facility-select-page::after {
      content: '';
      position: absolute;
      border-radius: 999px;
      pointer-events: none;
      filter: blur(18px);
    }
    .facility-select-page::before {
      width: 220px;
      height: 220px;
      top: 10%;
      left: 8%;
      background: var(--ops-highlight-soft);
    }
    .facility-select-page::after {
      width: 260px;
      height: 260px;
      right: -30px;
      bottom: -40px;
      background: var(--ops-primary-soft);
    }
    .theme-fab {
      position: absolute;
      top: 20px;
      right: 20px;
      color: var(--ops-text);
      background: var(--ops-glass-soft);
      border: 1px solid var(--ops-border);
      backdrop-filter: blur(14px);
      z-index: 2;
    }
    .facility-card {
      background: var(--ops-elevated-bg);
      border-radius: 28px;
      width: 100%;
      max-width: 400px;
      overflow: hidden;
      box-shadow: var(--ops-shadow);
      border: 1px solid var(--ops-card-border);
      backdrop-filter: blur(16px);
      position: relative;
      z-index: 1;
    }
    .card-header {
      text-align: center;
      padding: 32px 24px 20px;
    }
    .logo-circle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: var(--ops-avatar-bg);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 12px;
      box-shadow: var(--ops-avatar-shadow);
    }
    .logo-circle mat-icon {
      color: white;
      font-size: 28px;
      width: 28px;
      height: 28px;
    }
    h2 {
      font-size: 22px;
      font-weight: 700;
      color: var(--ops-text-primary);
      margin: 0 0 4px;
    }
    p {
      font-size: 14px;
      color: var(--ops-text-secondary);
      margin: 0;
    }
    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 24px;
    }
    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--ops-avatar-bg);
      color: var(--ops-primary-contrast);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
      flex-shrink: 0;
      box-shadow: var(--ops-avatar-shadow);
    }
    .user-name {
      font-weight: 600;
      font-size: 14px;
      color: var(--ops-text-primary);
    }
    .user-email {
      font-size: 12px;
      color: var(--ops-text-secondary);
    }
    .facilities-list {
      padding: 8px 0;
    }
    .list-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--ops-text-soft);
      padding: 8px 24px;
    }
    .facility-item {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 24px;
      background: none;
      border: none;
      cursor: pointer;
      transition: background 0.15s;
      text-align: left;
    }
    .facility-item:hover {
      background: var(--ops-item-hover);
    }
    .facility-item:active {
      background: var(--ops-item-active);
    }
    .facility-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: var(--ops-primary-soft);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .facility-icon mat-icon {
      color: var(--ops-primary);
    }
    .facility-info {
      flex: 1;
    }
    .facility-name {
      display: block;
      font-weight: 600;
      font-size: 14px;
      color: var(--ops-text-primary);
    }
    .facility-code {
      display: block;
      font-size: 12px;
      color: var(--ops-text-secondary);
    }
    .chevron {
      color: var(--ops-text-soft);
    }
    .empty-facilities {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
      gap: 8px;
      color: var(--ops-text-soft);
    }
    .empty-facilities mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
    }
    .logout-btn {
      width: calc(100% - 48px);
      margin: 16px 24px;
      color: var(--ops-text-secondary);
    }
    .menu-header {
      padding: 8px 16px;
      font-size: 12px;
      font-weight: 600;
      color: var(--ops-text-soft);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .active-theme {
      background: var(--ops-primary-soft);
      color: var(--ops-primary);
    }
  `]
})
export class FacilitySelectComponent {
  private auth = inject(AuthService);
  theme = inject(ThemeService);

  loading = signal(false);
  get facilities() { return this.auth.availableFacilities(); }
  get userName() { return this.auth.currentUser()?.display_name ?? ''; }
  get userEmail() { return this.auth.currentUser()?.email ?? ''; }
  get userInitials() {
    const name = this.userName;
    if (!name) return '?';
    const parts = name.trim().split(' ');
    return (parts[0][0] + (parts[1]?.[0] ?? '')).toUpperCase();
  }

  get themeIcon(): string {
    const preference = this.theme.preference();
    if (preference === 'light') return 'light_mode';
    if (preference === 'dark') return 'dark_mode';
    return 'brightness_auto';
  }

  get themeTooltip(): string {
    const preference = this.theme.preference();
    if (preference === 'light') return 'Theme: Light';
    if (preference === 'dark') return 'Theme: Dark';
    return 'Theme: System';
  }

  setTheme(preference: ThemePreference): void {
    this.theme.set(preference);
  }

  async selectFacility(facility: Facility): Promise<void> {
    this.loading.set(true);
    try {
      await this.auth.selectFacility(facility);
    } finally {
      this.loading.set(false);
    }
  }

  onLogout(): void {
    this.auth.logout();
  }
}

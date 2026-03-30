import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { AuthService } from '../../core/auth/auth.service';
import { Facility } from '../../core/models/user.model';

@Component({
  selector: 'app-facility-select',
  standalone: true,
  imports: [
    CommonModule, MatCardModule, MatButtonModule,
    MatIconModule, MatProgressSpinnerModule, MatDividerModule
  ],
  template: `
    <div class="facility-select-page">
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
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      padding: 16px;
    }
    .facility-card {
      background: white;
      border-radius: 20px;
      width: 100%;
      max-width: 400px;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .card-header {
      text-align: center;
      padding: 32px 24px 20px;
    }
    .logo-circle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 12px;
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
      color: #1e293b;
      margin: 0 0 4px;
    }
    p {
      font-size: 14px;
      color: #64748b;
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
      background: #3b82f6;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
      flex-shrink: 0;
    }
    .user-name {
      font-weight: 600;
      font-size: 14px;
      color: #1e293b;
    }
    .user-email {
      font-size: 12px;
      color: #64748b;
    }
    .facilities-list {
      padding: 8px 0;
    }
    .list-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #94a3b8;
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
      background: #f8fafc;
    }
    .facility-item:active {
      background: #eff6ff;
    }
    .facility-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: #eff6ff;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .facility-icon mat-icon {
      color: #3b82f6;
    }
    .facility-info {
      flex: 1;
    }
    .facility-name {
      display: block;
      font-weight: 600;
      font-size: 14px;
      color: #1e293b;
    }
    .facility-code {
      display: block;
      font-size: 12px;
      color: #64748b;
    }
    .chevron {
      color: #94a3b8;
    }
    .empty-facilities {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px;
      gap: 8px;
      color: #94a3b8;
    }
    .empty-facilities mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
    }
    .logout-btn {
      width: calc(100% - 48px);
      margin: 16px 24px;
      color: #64748b;
    }
  `]
})
export class FacilitySelectComponent {
  private auth = inject(AuthService);

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

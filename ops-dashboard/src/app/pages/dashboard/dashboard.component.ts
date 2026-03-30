import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../core/services/operations.service';
import { AuthService } from '../../core/auth/auth.service';

interface StatCard {
  label: string;
  value: string | number;
  icon: string;
  color: string;
  bg: string;
  route: string;
}

interface RecentTransaction {
  id: string;
  type: string;
  status: string;
  reference?: string;
  created_at: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MatIconModule,
    MatButtonModule, MatProgressSpinnerModule, PageHeaderComponent
  ],
  template: `
    <div class="dashboard">
      <app-page-header
        title="Dashboard"
        [description]="'Welcome back, ' + (auth.currentUser()?.display_name ?? 'User')"
        icon="dashboard">
      </app-page-header>

      <!-- Stats grid -->
      <div class="stats-grid">
        <a class="stat-card" *ngFor="let stat of stats()" [routerLink]="stat.route">
          <div class="stat-icon" [style.background]="stat.bg">
            <mat-icon [style.color]="stat.color">{{ stat.icon }}</mat-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
          <mat-icon class="stat-arrow">chevron_right</mat-icon>
        </a>
      </div>

      <!-- Quick actions -->
      <div class="section">
        <h3 class="section-title">Quick Actions</h3>
        <div class="quick-actions">
          <a class="quick-action-btn" routerLink="/transactions/grn">
            <div class="qa-icon" style="background:#dcfce7">
              <mat-icon style="color:#16a34a">input</mat-icon>
            </div>
            <span>New GRN</span>
          </a>
          <a class="quick-action-btn" routerLink="/transactions/move">
            <div class="qa-icon" style="background:#fef3c7">
              <mat-icon style="color:#d97706">swap_horiz</mat-icon>
            </div>
            <span>Move Stock</span>
          </a>
          <a class="quick-action-btn" routerLink="/transactions/putaway">
            <div class="qa-icon" style="background:#ede9fe">
              <mat-icon style="color:#7c3aed">move_to_inbox</mat-icon>
            </div>
            <span>Putaway</span>
          </a>
          <a class="quick-action-btn" routerLink="/transactions/order-pick">
            <div class="qa-icon" style="background:#fee2e2">
              <mat-icon style="color:#dc2626">shopping_cart</mat-icon>
            </div>
            <span>Order Pick</span>
          </a>
          <a class="quick-action-btn" routerLink="/inventory">
            <div class="qa-icon" style="background:#e0f2fe">
              <mat-icon style="color:#0284c7">inventory</mat-icon>
            </div>
            <span>Inventory</span>
          </a>
        </div>
      </div>

      <!-- Recent transactions -->
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">Recent Transactions</h3>
          <a routerLink="/transactions" class="see-all">See all</a>
        </div>

        <div class="loading-state" *ngIf="loadingTxns()">
          <mat-spinner diameter="32"></mat-spinner>
        </div>

        <div class="recent-list" *ngIf="!loadingTxns()">
          <div class="txn-item" *ngFor="let txn of recentTxns()">
            <div class="txn-type-icon" [style.background]="getTxnBg(txn.type)">
              <mat-icon [style.color]="getTxnColor(txn.type)">{{ getTxnIcon(txn.type) }}</mat-icon>
            </div>
            <div class="txn-info">
              <div class="txn-type">{{ txn.type }}</div>
              <div class="txn-ref">{{ txn.reference ?? txn.id.slice(0,8) + '...' }}</div>
            </div>
            <div class="txn-right">
              <span class="txn-status" [class]="'status-' + txn.status.toLowerCase()">
                {{ txn.status }}
              </span>
              <span class="txn-date">{{ txn.created_at | date:'dd MMM' }}</span>
            </div>
          </div>

          <div class="empty-recent" *ngIf="recentTxns().length === 0">
            <mat-icon>receipt_long</mat-icon>
            <p>No recent transactions</p>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard {
      padding-bottom: 24px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 12px;
      padding: 0 24px 24px;
    }
    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      text-decoration: none;
      color: inherit;
      transition: box-shadow 0.2s, transform 0.2s;
      cursor: pointer;
    }
    .stat-card:hover {
      box-shadow: 0 4px 12px rgba(0,0,0,0.12);
      transform: translateY(-2px);
    }
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .stat-content { flex: 1; }
    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: #1e293b;
      line-height: 1;
    }
    .stat-label {
      font-size: 12px;
      color: #64748b;
      margin-top: 4px;
    }
    .stat-arrow { color: #94a3b8; }
    .section {
      padding: 0 24px 24px;
    }
    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #1e293b;
      margin: 0 0 12px;
    }
    .see-all {
      font-size: 13px;
      color: #3b82f6;
      text-decoration: none;
    }
    .quick-actions {
      display: flex;
      gap: 12px;
      overflow-x: auto;
      padding-bottom: 4px;
    }
    .quick-action-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 16px 12px;
      background: white;
      border-radius: 12px;
      text-decoration: none;
      color: #334155;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      min-width: 80px;
      transition: transform 0.2s, box-shadow 0.2s;
      flex-shrink: 0;
    }
    .quick-action-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .qa-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .quick-action-btn span {
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }
    .loading-state {
      display: flex;
      justify-content: center;
      padding: 32px;
    }
    .recent-list {
      background: white;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      overflow: hidden;
    }
    .txn-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid #f1f5f9;
      transition: background 0.1s;
      cursor: pointer;
    }
    .txn-item:last-child { border-bottom: none; }
    .txn-item:hover { background: #f8fafc; }
    .txn-type-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .txn-info { flex: 1; }
    .txn-type {
      font-weight: 600;
      font-size: 14px;
      color: #1e293b;
    }
    .txn-ref {
      font-size: 12px;
      color: #64748b;
      font-family: monospace;
    }
    .txn-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
    }
    .txn-status {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 20px;
    }
    .status-completed { background: #dcfce7; color: #16a34a; }
    .status-pending { background: #fef3c7; color: #d97706; }
    .status-in_progress { background: #dbeafe; color: #2563eb; }
    .status-cancelled { background: #f1f5f9; color: #64748b; }
    .status-failed { background: #fef2f2; color: #ef4444; }
    .txn-date { font-size: 11px; color: #94a3b8; }
    .empty-recent {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      gap: 8px;
      color: #94a3b8;
    }
    .empty-recent mat-icon {
      font-size: 36px;
      width: 36px;
      height: 36px;
    }
    .empty-recent p { margin: 0; font-size: 14px; }

    @media (max-width: 600px) {
      .stats-grid { padding: 0 16px 16px; }
      .section { padding: 0 16px 16px; }
    }
  `]
})
export class DashboardComponent implements OnInit {
  auth = inject(AuthService);
  private ops = inject(OperationsService);

  stats = signal<StatCard[]>([
    { label: 'SKUs', value: '—', icon: 'inventory_2', color: '#3b82f6', bg: '#eff6ff', route: '/masters/sku' },
    { label: 'Zones', value: '—', icon: 'grid_view', color: '#8b5cf6', bg: '#f5f3ff', route: '/masters/zone' },
    { label: 'Locations', value: '—', icon: 'location_on', color: '#10b981', bg: '#ecfdf5', route: '/masters/location' },
    { label: 'Transactions', value: '—', icon: 'receipt_long', color: '#f59e0b', bg: '#fffbeb', route: '/transactions' },
  ]);

  recentTxns = signal<RecentTransaction[]>([]);
  loadingTxns = signal(true);

  ngOnInit(): void {
    this.loadRecentTransactions();
  }

  loadRecentTransactions(): void {
    this.loadingTxns.set(true);
    this.ops.getTransactions({ size: 5 }).subscribe({
      next: (res) => {
        const items = Array.isArray(res) ? res : res.items;
        this.recentTxns.set(items.slice(0, 5));
        this.loadingTxns.set(false);
      },
      error: () => this.loadingTxns.set(false)
    });
  }

  getTxnIcon(type: string): string {
    const map: Record<string, string> = {
      GRN: 'input', MOVE: 'swap_horiz', PUTAWAY: 'move_to_inbox',
      ORDER_PICK: 'shopping_cart', RETURN: 'undo', ADJUSTMENT: 'tune',
      CYCLE_COUNT: 'fact_check'
    };
    return map[type] ?? 'receipt';
  }

  getTxnColor(type: string): string {
    const map: Record<string, string> = {
      GRN: '#16a34a', MOVE: '#d97706', PUTAWAY: '#7c3aed',
      ORDER_PICK: '#dc2626', RETURN: '#0284c7', ADJUSTMENT: '#64748b'
    };
    return map[type] ?? '#334155';
  }

  getTxnBg(type: string): string {
    const map: Record<string, string> = {
      GRN: '#dcfce7', MOVE: '#fef3c7', PUTAWAY: '#ede9fe',
      ORDER_PICK: '#fee2e2', RETURN: '#e0f2fe', ADJUSTMENT: '#f1f5f9'
    };
    return map[type] ?? '#f1f5f9';
  }
}

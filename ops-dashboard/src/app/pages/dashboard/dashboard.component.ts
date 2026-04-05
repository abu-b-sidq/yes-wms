import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../core/services/operations.service';
import { MastersService } from '../../core/services/masters.service';
import { AuthService } from '../../core/auth/auth.service';
import { forkJoin } from 'rxjs';

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

interface QuickAction {
  label: string;
  icon: string;
  route: string;
  color: string;
  bg: string;
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
          <a class="quick-action-btn" *ngFor="let action of quickActions" [routerLink]="action.route">
            <div class="qa-icon" [style.background]="action.bg">
              <mat-icon [style.color]="action.color">{{ action.icon }}</mat-icon>
            </div>
            <span>{{ action.label }}</span>
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
      position: relative;
      padding-bottom: 24px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      padding: 0 24px 24px;
    }
    .stat-card {
      background: var(--ops-elevated-bg-soft);
      border: 1px solid var(--ops-border);
      border-radius: 18px;
      padding: 18px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: var(--ops-shadow);
      text-decoration: none;
      color: var(--ops-text);
      transition: border-color 0.2s, transform 0.2s, background 0.2s;
      cursor: pointer;
    }
    .stat-card:hover {
      border-color: var(--ops-border-strong);
      background: var(--ops-elevated-bg-hover);
      transform: translateY(-2px);
    }
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      border: 1px solid var(--ops-line-soft);
    }
    .stat-content { flex: 1; }
    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: var(--ops-text);
      line-height: 1;
    }
    .stat-label {
      font-size: 12px;
      color: var(--ops-text-muted);
      margin-top: 4px;
    }
    .stat-arrow { color: var(--ops-text-soft); }
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
      color: var(--ops-text);
      margin: 0 0 12px;
    }
    .see-all {
      font-size: 13px;
      color: var(--ops-primary);
      text-decoration: none;
    }
    .quick-actions {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
    }
    .quick-action-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 16px 12px;
      background: var(--ops-elevated-bg-soft);
      border: 1px solid var(--ops-border);
      border-radius: 18px;
      text-decoration: none;
      color: var(--ops-text);
      box-shadow: var(--ops-shadow);
      transition: transform 0.2s, border-color 0.2s, background 0.2s;
    }
    .quick-action-btn:hover {
      transform: translateY(-2px);
      border-color: var(--ops-border-strong);
      background: var(--ops-elevated-bg-hover);
    }
    .qa-icon {
      width: 48px;
      height: 48px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--ops-line-soft);
    }
    .quick-action-btn span {
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .loading-state {
      display: flex;
      justify-content: center;
      padding: 32px;
    }
    .recent-list {
      background: var(--ops-elevated-bg);
      border: 1px solid var(--ops-border);
      border-radius: 18px;
      box-shadow: var(--ops-shadow);
      overflow: hidden;
    }
    .txn-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--ops-border);
      transition: background 0.1s;
      cursor: pointer;
    }
    .txn-item:last-child { border-bottom: none; }
    .txn-item:hover { background: var(--ops-row-hover); }
    .txn-type-icon {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      border: 1px solid var(--ops-line-softer);
    }
    .txn-info { flex: 1; }
    .txn-type {
      font-weight: 600;
      font-size: 14px;
      color: var(--ops-text);
    }
    .txn-ref {
      font-size: 12px;
      color: var(--ops-text-muted);
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
      padding: 4px 10px;
      border-radius: 20px;
      border: 1px solid transparent;
    }
    .status-completed { background: var(--ops-success-soft); color: var(--ops-success-strong); border-color: var(--ops-success-soft); }
    .status-pending { background: var(--ops-warning-soft); color: var(--ops-warning-strong); border-color: var(--ops-warning-soft); }
    .status-in_progress { background: var(--ops-primary-soft); color: var(--ops-primary); border-color: var(--ops-primary-soft); }
    .status-cancelled { background: var(--ops-item-hover); color: var(--ops-text-muted); border-color: var(--ops-border); }
    .status-failed { background: var(--ops-danger-soft); color: var(--ops-danger-strong); border-color: var(--ops-danger-soft); }
    .txn-date { font-size: 11px; color: var(--ops-text-soft); }
    .empty-recent {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      gap: 8px;
      color: var(--ops-text-soft);
    }
    .empty-recent mat-icon {
      font-size: 36px;
      width: 36px;
      height: 36px;
    }
    .empty-recent p { margin: 0; font-size: 14px; }

    @media (max-width: 600px) {
      .stats-grid { padding: 0 16px 16px; grid-template-columns: repeat(2, 1fr); }
      .quick-actions { grid-template-columns: repeat(3, 1fr); }
      .section { padding: 0 16px 16px; }
    }
  `]
})
export class DashboardComponent implements OnInit {
  auth = inject(AuthService);
  private ops = inject(OperationsService);
  private masters = inject(MastersService);

  stats = signal<StatCard[]>([
    { label: 'SKUs', value: '—', icon: 'inventory_2', color: 'var(--ops-accent-blue)', bg: 'var(--ops-accent-blue-soft)', route: '/masters/sku' },
    { label: 'Zones', value: '—', icon: 'grid_view', color: 'var(--ops-accent-violet)', bg: 'var(--ops-accent-violet-soft)', route: '/masters/zone' },
    { label: 'Locations', value: '—', icon: 'location_on', color: 'var(--ops-success)', bg: 'var(--ops-success-soft)', route: '/masters/location' },
    { label: 'Transactions', value: '—', icon: 'receipt_long', color: 'var(--ops-accent-amber)', bg: 'var(--ops-accent-amber-soft)', route: '/transactions' },
  ]);

  quickActions: QuickAction[] = [
    { label: 'New GRN', icon: 'input', route: '/transactions/grn', color: 'var(--ops-success)', bg: 'var(--ops-success-soft)' },
    { label: 'Move Stock', icon: 'swap_horiz', route: '/transactions/move', color: 'var(--ops-accent-amber)', bg: 'var(--ops-accent-amber-soft)' },
    { label: 'Putaway', icon: 'move_to_inbox', route: '/transactions/putaway', color: 'var(--ops-accent-violet)', bg: 'var(--ops-accent-violet-soft)' },
    { label: 'Order Pick', icon: 'shopping_cart', route: '/transactions/order-pick', color: 'var(--ops-danger)', bg: 'var(--ops-danger-soft)' },
    { label: 'Inventory', icon: 'inventory', route: '/inventory', color: 'var(--ops-primary)', bg: 'var(--ops-primary-soft)' }
  ];

  recentTxns = signal<RecentTransaction[]>([]);
  loadingTxns = signal(true);

  ngOnInit(): void {
    this.loadStats();
    this.loadRecentTransactions();
  }

  loadStats(): void {
    forkJoin({
      skus: this.masters.getSkus({ page: 1, size: 1 }),
      zones: this.masters.getZones({ page: 1, size: 1 }),
      locations: this.masters.getLocations({ page: 1, size: 1 }),
      txns: this.ops.getTransactions({ size: 1 }),
    }).subscribe({
      next: ({ skus, zones, locations, txns }) => {
        const getTotal = (r: any) => (Array.isArray(r) ? r.length : r.total);
        this.stats.update(s => s.map(card => {
          if (card.label === 'SKUs') return { ...card, value: getTotal(skus) };
          if (card.label === 'Zones') return { ...card, value: getTotal(zones) };
          if (card.label === 'Locations') return { ...card, value: getTotal(locations) };
          if (card.label === 'Transactions') return { ...card, value: getTotal(txns) };
          return card;
        }));
      }
    });
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
      GRN: 'var(--ops-success)',
      MOVE: 'var(--ops-accent-amber)',
      PUTAWAY: 'var(--ops-accent-violet)',
      ORDER_PICK: 'var(--ops-danger)',
      RETURN: 'var(--ops-accent-blue)',
      ADJUSTMENT: 'var(--ops-text-muted)'
    };
    return map[type] ?? 'var(--ops-text-muted)';
  }

  getTxnBg(type: string): string {
    const map: Record<string, string> = {
      GRN: 'var(--ops-success-soft)',
      MOVE: 'var(--ops-accent-amber-soft)',
      PUTAWAY: 'var(--ops-accent-violet-soft)',
      ORDER_PICK: 'var(--ops-danger-soft)',
      RETURN: 'var(--ops-accent-blue-soft)',
      ADJUSTMENT: 'var(--ops-item-hover)'
    };
    return map[type] ?? 'var(--ops-item-hover)';
  }
}

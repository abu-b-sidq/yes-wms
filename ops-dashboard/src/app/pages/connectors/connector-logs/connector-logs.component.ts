import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { ConnectorsService } from '../../../core/services/connectors.service';
import { ConnectorConfig, SyncLog, ENTITY_TYPE_LABELS, SYNC_STATUS_CONFIG } from '../../../core/models/connector.model';

@Component({
  selector: 'app-connector-logs',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule, MatIconModule, MatProgressSpinnerModule,
    MatTooltipModule, MatSnackBarModule,
    PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header
        [title]="connector()?.name ?? 'Sync Logs'"
        description="Sync history for this connector"
        icon="history">
        <div class="header-actions">
          <button mat-stroked-button (click)="onBack()">
            <mat-icon>arrow_back</mat-icon> Back
          </button>
          <button mat-flat-button color="primary" (click)="onSync()" [disabled]="syncing()">
            <mat-icon>sync</mat-icon> {{ syncing() ? 'Syncing...' : 'Sync Now' }}
          </button>
        </div>
      </app-page-header>

      <div class="content-area">

        <!-- Connector info banner -->
        <div class="connector-banner" *ngIf="connector()">
          <div class="banner-item">
            <span class="banner-label">System</span>
            <span class="banner-value">{{ connector()!.connector_type }}</span>
          </div>
          <div class="banner-item">
            <span class="banner-label">Status</span>
            <span class="status-badge" [class.active]="connector()!.is_active" [class.inactive]="!connector()!.is_active">
              {{ connector()!.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="banner-item">
            <span class="banner-label">Sync Interval</span>
            <span class="banner-value">Every {{ connector()!.sync_interval_minutes }} min</span>
          </div>
          <div class="banner-item">
            <span class="banner-label">Last Synced</span>
            <span class="banner-value">
              {{ connector()!.last_synced_at ? (connector()!.last_synced_at | date:'dd MMM yyyy, HH:mm') : 'Never' }}
            </span>
          </div>
        </div>

        <div class="center-spinner" *ngIf="loading()">
          <mat-spinner diameter="40"></mat-spinner>
        </div>

        <div class="empty-state" *ngIf="!loading() && logs().length === 0">
          <mat-icon class="empty-icon">sync_disabled</mat-icon>
          <p class="empty-title">No sync logs yet</p>
          <p class="empty-sub">Run a sync to see history here.</p>
        </div>

        <!-- Logs grouped by run -->
        <div class="logs-list" *ngIf="!loading() && logs().length > 0">

          <!-- Summary row -->
          <div class="logs-summary">
            <span class="summary-count">{{ logs().length }} sync run{{ logs().length !== 1 ? 's' : '' }}</span>
            <button mat-button (click)="loadLogs()">
              <mat-icon>refresh</mat-icon> Refresh
            </button>
          </div>

          <div class="log-card" *ngFor="let log of logs()">
            <div class="log-header">
              <div class="log-entity">
                <mat-icon class="entity-icon">{{ entityIcon(log.entity_type) }}</mat-icon>
                <span class="entity-name">{{ entityLabels[log.entity_type] }}</span>
              </div>
              <span class="log-status"
                    [style.color]="statusConfig[log.status].color"
                    [style.background]="statusConfig[log.status].bg">
                {{ log.status }}
              </span>
            </div>

            <div class="log-stats">
              <div class="stat">
                <span class="stat-num">{{ log.records_fetched }}</span>
                <span class="stat-label">Fetched</span>
              </div>
              <div class="stat created">
                <span class="stat-num">{{ log.records_created }}</span>
                <span class="stat-label">Created</span>
              </div>
              <div class="stat updated">
                <span class="stat-num">{{ log.records_updated }}</span>
                <span class="stat-label">Updated</span>
              </div>
              <div class="stat">
                <span class="stat-num">{{ log.records_skipped }}</span>
                <span class="stat-label">Skipped</span>
              </div>
              <div class="stat failed" *ngIf="log.records_failed > 0">
                <span class="stat-num">{{ log.records_failed }}</span>
                <span class="stat-label">Failed</span>
              </div>
            </div>

            <div class="log-time">
              <span>{{ log.created_at | date:'dd MMM yyyy, HH:mm:ss' }}</span>
              <span *ngIf="log.started_at && log.completed_at" class="duration">
                &nbsp;·&nbsp;{{ getDuration(log.started_at, log.completed_at) }}
              </span>
            </div>

            <!-- Error details (collapsible) -->
            <div class="log-errors" *ngIf="log.error_details && log.error_details.length > 0">
              <details>
                <summary class="errors-summary">
                  <mat-icon style="font-size:14px;vertical-align:middle;color:#dc2626">error_outline</mat-icon>
                  {{ log.error_details.length }} error{{ log.error_details.length !== 1 ? 's' : '' }}
                </summary>
                <div class="error-list">
                  <div class="error-item" *ngFor="let e of log.error_details">
                    <span class="error-id" *ngIf="e.external_id">{{ e.external_id }}</span>
                    <span class="error-msg">{{ e.error }}</span>
                  </div>
                </div>
              </details>
            </div>

          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .content-area { padding: 0 24px 24px; display: flex; flex-direction: column; gap: 16px; }
    .header-actions { display: flex; gap: 8px; }

    .connector-banner {
      display: flex; flex-wrap: wrap; gap: 24px;
      background: white; border: 1px solid #e2e8f0;
      border-radius: 10px; padding: 16px 20px;
    }
    .banner-item { display: flex; flex-direction: column; gap: 3px; }
    .banner-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.06em; }
    .banner-value { font-size: 14px; color: #1e293b; font-weight: 500; }

    .status-badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
    .status-badge.active { background: #dcfce7; color: #16a34a; }
    .status-badge.inactive { background: #f1f5f9; color: #64748b; }

    .center-spinner { display: flex; justify-content: center; padding: 48px; }

    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      gap: 10px; padding: 48px; text-align: center;
    }
    .empty-icon { font-size: 48px; width: 48px; height: 48px; color: #cbd5e1; }
    .empty-title { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0; }
    .empty-sub { font-size: 13px; color: #64748b; margin: 0; }

    .logs-list { display: flex; flex-direction: column; gap: 10px; }
    .logs-summary {
      display: flex; justify-content: space-between; align-items: center;
      font-size: 13px; color: #64748b;
    }

    .log-card {
      background: white; border: 1px solid #e2e8f0;
      border-radius: 10px; padding: 16px; display: flex;
      flex-direction: column; gap: 12px;
    }

    .log-header { display: flex; justify-content: space-between; align-items: center; }
    .log-entity { display: flex; align-items: center; gap: 8px; }
    .entity-icon { font-size: 18px; width: 18px; height: 18px; color: #64748b; }
    .entity-name { font-size: 14px; font-weight: 600; color: #1e293b; }
    .log-status {
      font-size: 11px; font-weight: 700; padding: 3px 10px;
      border-radius: 20px; text-transform: uppercase;
    }

    .log-stats { display: flex; gap: 20px; }
    .stat { display: flex; flex-direction: column; align-items: center; gap: 2px; }
    .stat-num { font-size: 20px; font-weight: 700; color: #1e293b; }
    .stat-label { font-size: 11px; color: #94a3b8; }
    .stat.created .stat-num { color: #16a34a; }
    .stat.updated .stat-num { color: #2563eb; }
    .stat.failed .stat-num { color: #dc2626; }

    .log-time { font-size: 12px; color: #94a3b8; }
    .duration { color: #94a3b8; }

    .log-errors { border-top: 1px solid #f1f5f9; padding-top: 10px; }
    .errors-summary { font-size: 13px; color: #dc2626; cursor: pointer; list-style: none; }
    .error-list { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
    .error-item {
      background: #fef2f2; border-radius: 6px; padding: 8px 10px;
      display: flex; flex-direction: column; gap: 2px;
    }
    .error-id { font-size: 11px; font-family: monospace; color: #64748b; }
    .error-msg { font-size: 12px; color: #dc2626; }

    @media (max-width: 600px) {
      .content-area { padding: 0 12px 16px; }
      .log-stats { gap: 12px; flex-wrap: wrap; }
    }
  `]
})
export class ConnectorLogsComponent implements OnInit {
  private svc = inject(ConnectorsService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private snack = inject(MatSnackBar);

  connectorId = '';
  connector = signal<ConnectorConfig | null>(null);
  logs = signal<SyncLog[]>([]);
  loading = signal(true);
  syncing = signal(false);

  entityLabels = ENTITY_TYPE_LABELS;
  statusConfig = SYNC_STATUS_CONFIG;

  ngOnInit(): void {
    this.connectorId = this.route.snapshot.paramMap.get('id') ?? '';
    this.svc.getById(this.connectorId).subscribe({
      next: (c) => this.connector.set(c),
      error: () => {}
    });
    this.loadLogs();
  }

  loadLogs(): void {
    this.loading.set(true);
    this.svc.getLogs(this.connectorId).subscribe({
      next: (logs) => { this.logs.set(logs); this.loading.set(false); },
      error: () => { this.snack.open('Failed to load logs', 'Dismiss', { duration: 3000 }); this.loading.set(false); }
    });
  }

  onSync(): void {
    this.syncing.set(true);
    this.svc.triggerSync(this.connectorId).subscribe({
      next: (logs) => {
        this.syncing.set(false);
        const total = logs.reduce((s, l) => s + l.records_created + l.records_updated, 0);
        this.snack.open(`Sync complete — ${total} records processed`, 'Dismiss', { duration: 4000 });
        this.loadLogs();
        this.svc.getById(this.connectorId).subscribe(c => this.connector.set(c));
      },
      error: () => {
        this.syncing.set(false);
        this.snack.open('Sync failed', 'Dismiss', { duration: 4000 });
      }
    });
  }

  onBack(): void {
    this.router.navigate(['/connectors']);
  }

  entityIcon(type: string): string {
    const icons: Record<string, string> = {
      SKU: 'inventory_2',
      INVENTORY: 'inventory',
      ORDER: 'shopping_cart',
      PURCHASE_ORDER: 'input',
      SUPPLIER: 'local_shipping',
      CUSTOMER: 'person'
    };
    return icons[type] ?? 'sync';
  }

  getDuration(start: string, end: string): string {
    const ms = new Date(end).getTime() - new Date(start).getTime();
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
  }
}

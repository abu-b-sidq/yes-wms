import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DetailDialogComponent } from '../../shared/components/detail-dialog/detail-dialog.component';
import { ConnectorsService } from '../../core/services/connectors.service';
import {
  ConnectorConfig, ConnectorType, SyncEntityType,
  CONNECTOR_CONFIG_TEMPLATES, ENTITY_TYPE_LABELS, SYNC_STATUS_CONFIG
} from '../../core/models/connector.model';

const CONNECTOR_TYPES: { value: ConnectorType; label: string; icon: string }[] = [
  { value: 'STOCKONE', label: 'StockOne', icon: 'hub' },
  { value: 'SAP',      label: 'SAP',      icon: 'hub' },
  { value: 'ORACLE',   label: 'Oracle',   icon: 'hub' }
];

const ALL_ENTITIES: SyncEntityType[] = ['SKU', 'INVENTORY', 'ORDER', 'PURCHASE_ORDER', 'SUPPLIER', 'CUSTOMER'];

@Component({
  selector: 'app-connectors',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSlideToggleModule,
    MatCheckboxModule, MatSnackBarModule, MatChipsModule,
    MatProgressSpinnerModule, MatTooltipModule,
    PageHeaderComponent, DetailDialogComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header
        title="Integrations"
        description="Connect external WMS systems and sync data into YES WMS"
        icon="hub">
        <button mat-flat-button color="primary" (click)="openForm()">
          <mat-icon>add</mat-icon> New Connector
        </button>
      </app-page-header>

      <div class="content-area">

        <!-- Loading -->
        <div class="center-spinner" *ngIf="loading()">
          <mat-spinner diameter="40"></mat-spinner>
        </div>

        <!-- Empty state -->
        <div class="empty-state" *ngIf="!loading() && connectors().length === 0">
          <mat-icon class="empty-icon">cable</mat-icon>
          <p class="empty-title">No connectors configured</p>
          <p class="empty-sub">Connect an external WMS to start syncing data automatically.</p>
          <button mat-flat-button color="primary" (click)="openForm()">
            <mat-icon>add</mat-icon> Add Connector
          </button>
        </div>

        <!-- Connector cards -->
        <div class="connector-grid" *ngIf="!loading() && connectors().length > 0">
          <div class="connector-card" *ngFor="let c of connectors()">

            <div class="card-header">
              <div class="card-title-row">
                <div class="connector-icon">
                  <mat-icon>hub</mat-icon>
                </div>
                <div class="card-title-info">
                  <span class="card-name">{{ c.name }}</span>
                  <span class="card-type">{{ c.connector_type }}</span>
                </div>
              </div>
              <div class="card-status">
                <span class="status-badge" [class.active]="c.is_active" [class.inactive]="!c.is_active">
                  {{ c.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>

            <div class="card-meta">
              <div class="meta-row">
                <mat-icon class="meta-icon">sync</mat-icon>
                <span>Every {{ c.sync_interval_minutes }} min</span>
              </div>
              <div class="meta-row" *ngIf="c.last_synced_at">
                <mat-icon class="meta-icon">schedule</mat-icon>
                <span>Last synced {{ c.last_synced_at | date:'dd MMM, HH:mm' }}</span>
              </div>
              <div class="meta-row" *ngIf="!c.last_synced_at">
                <mat-icon class="meta-icon">schedule</mat-icon>
                <span class="never-synced">Never synced</span>
              </div>
            </div>

            <div class="entity-chips">
              <span class="entity-chip" *ngFor="let e of c.enabled_entities">
                {{ entityLabels[e] }}
              </span>
            </div>

            <div class="card-actions">
              <button mat-stroked-button (click)="onTest(c)" [disabled]="testing() === c.id" class="action-btn">
                <mat-icon>wifi_tethering</mat-icon>
                {{ testing() === c.id ? 'Testing...' : 'Test' }}
              </button>
              <button mat-stroked-button color="primary" (click)="onSync(c)" [disabled]="syncing() === c.id" class="action-btn">
                <mat-icon>sync</mat-icon>
                {{ syncing() === c.id ? 'Syncing...' : 'Sync Now' }}
              </button>
              <button mat-icon-button (click)="viewLogs(c)" matTooltip="View sync logs">
                <mat-icon>history</mat-icon>
              </button>
              <button mat-icon-button (click)="openForm(c)" matTooltip="Edit connector">
                <mat-icon>edit</mat-icon>
              </button>
              <button mat-icon-button color="warn" (click)="onDeactivate(c)"
                      *ngIf="c.is_active" matTooltip="Deactivate">
                <mat-icon>power_settings_new</mat-icon>
              </button>
            </div>

          </div>
        </div>
      </div>

      <!-- Create / Edit dialog -->
      <app-detail-dialog
        [open]="formOpen()"
        [title]="editing() ? 'Edit Connector' : 'New Connector'"
        [showFooter]="true"
        (closed)="formOpen.set(false)">

        <form [formGroup]="form" class="form-body">

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Connector Name *</mat-label>
            <input matInput formControlName="name" placeholder="e.g. StockOne Production">
            <mat-error>Required</mat-error>
          </mat-form-field>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>System Type *</mat-label>
            <mat-select formControlName="connector_type" (selectionChange)="onTypeChange($event.value)">
              <mat-option *ngFor="let t of connectorTypes" [value]="t.value">
                <mat-icon style="font-size:16px;vertical-align:middle;margin-right:6px">{{ t.icon }}</mat-icon>
                {{ t.label }}
              </mat-option>
            </mat-select>
            <mat-error>Required</mat-error>
          </mat-form-field>

          <!-- Dynamic config fields -->
          <div class="config-section" *ngIf="configKeys().length">
            <div class="section-label">Connection Settings</div>
            <mat-form-field appearance="outline" class="full-width" *ngFor="let key of configKeys()">
              <mat-label>{{ formatConfigKey(key) }}</mat-label>
              <input matInput [formControlName]="'config_' + key"
                     [type]="isSecret(key) ? 'password' : 'text'"
                     [placeholder]="getConfigPlaceholder(key)">
            </mat-form-field>
          </div>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Sync Interval (minutes)</mat-label>
            <input matInput type="number" formControlName="sync_interval_minutes" min="5">
          </mat-form-field>

          <!-- Entity selection -->
          <div class="entities-section">
            <div class="section-label">Entities to Sync</div>
            <div class="entity-checks">
              <mat-checkbox *ngFor="let e of allEntities"
                            [checked]="isEntityEnabled(e)"
                            (change)="toggleEntity(e, $event.checked)">
                {{ entityLabels[e] }}
              </mat-checkbox>
            </div>
          </div>

        </form>

        <div footer-actions>
          <button mat-flat-button color="primary" (click)="onSave()" [disabled]="saving()">
            {{ saving() ? 'Saving...' : (editing() ? 'Update' : 'Create Connector') }}
          </button>
        </div>
      </app-detail-dialog>

    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .content-area { padding: 0 24px 24px; }

    .center-spinner { display: flex; justify-content: center; padding: 48px; }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      padding: 64px 24px;
      text-align: center;
    }
    .empty-icon { font-size: 56px; width: 56px; height: 56px; color: var(--ops-text-soft); }
    .empty-title { font-size: 18px; font-weight: 600; color: var(--ops-text-primary); margin: 0; }
    .empty-sub { font-size: 14px; color: var(--ops-text-secondary); margin: 0; }

    .connector-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
    }

    .connector-card {
      background: var(--ops-card-bg);
      border: 1px solid var(--ops-card-border);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
    }
    .connector-card:hover {
      box-shadow: var(--ops-shadow-soft);
      transform: translateY(-2px);
      border-color: var(--ops-border-strong);
    }

    .card-header { display: flex; justify-content: space-between; align-items: flex-start; }
    .card-title-row { display: flex; align-items: center; gap: 12px; }
    .connector-icon {
      width: 40px; height: 40px;
      background: var(--ops-primary-soft);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .connector-icon mat-icon { color: var(--ops-primary); }
    .card-title-info { display: flex; flex-direction: column; gap: 2px; }
    .card-name { font-size: 15px; font-weight: 600; color: var(--ops-text-primary); }
    .card-type { font-size: 12px; color: var(--ops-text-secondary); }

    .status-badge {
      font-size: 11px; font-weight: 600;
      padding: 3px 10px; border-radius: 20px;
    }
    .status-badge.active { background: var(--ops-success-soft); color: var(--ops-success); }
    .status-badge.inactive { background: var(--ops-surface-muted); color: var(--ops-text-soft); }

    .card-meta { display: flex; flex-direction: column; gap: 6px; }
    .meta-row { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--ops-text-secondary); }
    .meta-icon { font-size: 14px; width: 14px; height: 14px; }
    .never-synced { color: var(--ops-text-soft); font-style: italic; }

    .entity-chips { display: flex; flex-wrap: wrap; gap: 6px; }
    .entity-chip {
      font-size: 11px; padding: 3px 9px;
      background: var(--ops-item-hover); color: var(--ops-text-muted);
      border-radius: 20px; white-space: nowrap;
      border: 1px solid var(--ops-line-soft);
    }

    .card-actions {
      display: flex; align-items: center; gap: 6px;
      border-top: 1px solid var(--ops-card-border); padding-top: 12px;
    }
    .action-btn { font-size: 13px; }
    .action-btn mat-icon { font-size: 16px; width: 16px; height: 16px; margin-right: 4px; }

    /* Form styles */
    .form-body { display: flex; flex-direction: column; gap: 4px; }
    .full-width { width: 100%; }
    .config-section, .entities-section { display: flex; flex-direction: column; gap: 4px; }
    .section-label {
      font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.08em; color: var(--ops-text-secondary);
      padding: 8px 0 4px;
    }
    .entity-checks { display: flex; flex-direction: column; gap: 6px; padding: 4px 0; }

    @media (max-width: 600px) {
      .content-area { padding: 0 12px 16px; }
      .connector-grid { grid-template-columns: 1fr; }
    }
  `]
})
export class ConnectorsComponent implements OnInit {
  private svc = inject(ConnectorsService);
  private snack = inject(MatSnackBar);
  private router = inject(Router);
  private fb = inject(FormBuilder);

  connectors = signal<ConnectorConfig[]>([]);
  loading = signal(true);
  testing = signal<string | null>(null);
  syncing = signal<string | null>(null);
  saving = signal(false);
  formOpen = signal(false);
  editing = signal<ConnectorConfig | null>(null);
  configKeys = signal<string[]>([]);
  selectedEntities = signal<Set<SyncEntityType>>(new Set());

  connectorTypes = CONNECTOR_TYPES;
  allEntities = ALL_ENTITIES;
  entityLabels = ENTITY_TYPE_LABELS;

  form = this.fb.group({
    name: ['', Validators.required],
    connector_type: ['STOCKONE', Validators.required],
    sync_interval_minutes: [60]
  });

  ngOnInit(): void {
    this.loadConnectors();
  }

  loadConnectors(): void {
    this.loading.set(true);
    this.svc.list().subscribe({
      next: (list) => { this.connectors.set(list); this.loading.set(false); },
      error: () => { this.snack.open('Failed to load connectors', 'Dismiss', { duration: 3000 }); this.loading.set(false); }
    });
  }

  openForm(connector?: ConnectorConfig): void {
    this.editing.set(connector ?? null);
    const type: ConnectorType = (connector?.connector_type ?? 'STOCKONE') as ConnectorType;
    this.selectedEntities.set(new Set((connector?.enabled_entities ?? []) as SyncEntityType[]));
    this.rebuildConfigFields(type, connector?.config ?? {});

    this.form.patchValue({
      name: connector?.name ?? '',
      connector_type: type,
      sync_interval_minutes: connector?.sync_interval_minutes ?? 60
    });
    this.formOpen.set(true);
  }

  onTypeChange(type: ConnectorType): void {
    this.rebuildConfigFields(type, {});
  }

  private rebuildConfigFields(type: ConnectorType, existing: Record<string, unknown>): void {
    const template = CONNECTOR_CONFIG_TEMPLATES[type] ?? {};
    const keys = Object.keys(template);
    this.configKeys.set(keys);

    // Remove old config controls
    Object.keys(this.form.controls).filter(k => k.startsWith('config_')).forEach(k => {
      (this.form as any).removeControl(k);
    });

    // Add new ones
    keys.forEach(key => {
      (this.form as any).addControl('config_' + key, this.fb.control(existing[key] ?? template[key] ?? ''));
    });
  }

  formatConfigKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  isSecret(key: string): boolean {
    return key.includes('secret') || key.includes('password') || key.includes('token');
  }

  getConfigPlaceholder(key: string): string {
    const placeholders: Record<string, string> = {
      base_url: 'https://alpha-backend.stockone.com',
      warehouse_key: 'e.g. BLR01'
    };
    return placeholders[key] ?? '';
  }

  isEntityEnabled(e: SyncEntityType): boolean {
    return this.selectedEntities().has(e);
  }

  toggleEntity(e: SyncEntityType, checked: boolean): void {
    const s = new Set(this.selectedEntities());
    if (checked) s.add(e); else s.delete(e);
    this.selectedEntities.set(s);
  }

  onSave(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);

    const val = this.form.getRawValue() as Record<string, unknown>;
    const config: Record<string, string> = {};
    this.configKeys().forEach(k => { config[k] = val['config_' + k] as string; });

    const payload = {
      name: val['name'] as string,
      connector_type: val['connector_type'] as ConnectorType,
      config,
      sync_interval_minutes: Number(val['sync_interval_minutes']),
      enabled_entities: [...this.selectedEntities()]
    };

    const obs = this.editing()
      ? this.svc.update(this.editing()!.id, payload)
      : this.svc.create(payload);

    obs.subscribe({
      next: () => {
        this.snack.open(`Connector ${this.editing() ? 'updated' : 'created'}`, 'Dismiss', { duration: 3000 });
        this.formOpen.set(false);
        this.saving.set(false);
        this.loadConnectors();
      },
      error: () => {
        this.snack.open('Failed to save connector', 'Dismiss', { duration: 3000 });
        this.saving.set(false);
      }
    });
  }

  onTest(c: ConnectorConfig): void {
    this.testing.set(c.id);
    this.svc.testConnection(c.id).subscribe({
      next: (res) => {
        this.testing.set(null);
        this.snack.open(`Connection OK — scope: ${res.scope ?? 'n/a'}`, 'Dismiss', { duration: 4000 });
      },
      error: () => {
        this.testing.set(null);
        this.snack.open('Connection test failed', 'Dismiss', { duration: 4000, panelClass: ['snack-error'] });
      }
    });
  }

  onSync(c: ConnectorConfig): void {
    this.syncing.set(c.id);
    this.svc.triggerSync(c.id).subscribe({
      next: (logs) => {
        this.syncing.set(null);
        const total = logs.reduce((s, l) => s + l.records_created + l.records_updated, 0);
        this.snack.open(`Sync complete — ${total} records processed`, 'Dismiss', { duration: 4000 });
        this.loadConnectors();
      },
      error: () => {
        this.syncing.set(null);
        this.snack.open('Sync failed', 'Dismiss', { duration: 4000, panelClass: ['snack-error'] });
      }
    });
  }

  onDeactivate(c: ConnectorConfig): void {
    this.svc.deactivate(c.id).subscribe({
      next: () => {
        this.snack.open('Connector deactivated', 'Dismiss', { duration: 3000 });
        this.loadConnectors();
      },
      error: () => this.snack.open('Failed to deactivate', 'Dismiss', { duration: 3000 })
    });
  }

  viewLogs(c: ConnectorConfig): void {
    this.router.navigate(['/connectors', c.id, 'logs']);
  }
}

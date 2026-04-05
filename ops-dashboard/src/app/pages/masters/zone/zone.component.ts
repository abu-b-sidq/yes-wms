import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DataTableComponent, TableColumn, TableAction } from '../../../shared/components/data-table/data-table.component';
import { DetailDialogComponent } from '../../../shared/components/detail-dialog/detail-dialog.component';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { MastersService } from '../../../core/services/masters.service';
import { AuthService } from '../../../core/auth/auth.service';
import { Zone } from '../../../core/models/masters.model';

const ZONE_TYPES = ['STORAGE', 'PRE_PUTAWAY', 'STAGING', 'RETURNS', 'QUARANTINE', 'DISPATCH', 'OTHER'];

@Component({
  selector: 'app-zone',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSnackBarModule,
    DataTableComponent, DetailDialogComponent, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="Zones" description="Manage warehouse zones" icon="grid_view">
      </app-page-header>

      <div class="content-area">
        <app-data-table
          title="Zones"
          [columns]="columns"
          [dataSource]="zones()"
          [actions]="tableActions"
          [loading]="loading()"
          [totalItems]="total()"
          [pageSize]="pageSize"
          [pageIndex]="pageIndex()"
          [canCreate]="canManage"
          addLabel="Add Zone"
          (rowClick)="onView($any($event))"
          (actionClick)="onTableAction($event)"
          (addClick)="openForm()"
          (pageChange)="onPage($event)"
          (search)="onSearch($event)">
        </app-data-table>
      </div>

      <!-- View dialog -->
      <app-detail-dialog
        [open]="viewDialogOpen()"
        [title]="selectedZone()?.name ?? ''"
        [subtitle]="selectedZone()?.code ?? ''"
        (closed)="viewDialogOpen.set(false)">
        <div header-actions>
          <button mat-icon-button color="primary" (click)="openForm(selectedZone()!)" *ngIf="canManage">
            <mat-icon>edit</mat-icon>
          </button>
        </div>
        <div class="detail-grid" *ngIf="selectedZone()">
          <div class="detail-row"><span class="detail-label">Code</span><span class="detail-value mono">{{ selectedZone()!.code }}</span></div>
          <div class="detail-row"><span class="detail-label">Name</span><span class="detail-value">{{ selectedZone()!.name }}</span></div>
          <div class="detail-row"><span class="detail-label">Zone Type</span><span class="detail-value">{{ selectedZone()!.zone_type || '—' }}</span></div>
          <div class="detail-row">
            <span class="detail-label">Status</span>
            <span class="badge" [class.active]="selectedZone()!.is_active" [class.inactive]="!selectedZone()!.is_active">
              {{ selectedZone()!.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="detail-row"><span class="detail-label">Created</span><span class="detail-value">{{ selectedZone()!.created_at | date:'dd MMM yyyy, HH:mm' }}</span></div>
        </div>
      </app-detail-dialog>

      <!-- Form dialog -->
      <app-detail-dialog
        [open]="formDialogOpen()"
        [title]="editingZone() ? 'Edit Zone' : 'New Zone'"
        [showFooter]="true"
        (closed)="formDialogOpen.set(false)">
        <form [formGroup]="form" class="form-body">
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Zone Code *</mat-label>
            <input matInput formControlName="code" placeholder="e.g. ZONE-A" [readonly]="!!editingZone()">
            <mat-error>Required</mat-error>
          </mat-form-field>
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Name *</mat-label>
            <input matInput formControlName="name" placeholder="Zone name">
            <mat-error>Required</mat-error>
          </mat-form-field>
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Zone Type</mat-label>
            <mat-select formControlName="zone_type">
              <mat-option value="">— None —</mat-option>
              <mat-option *ngFor="let t of zoneTypes" [value]="t">{{ t }}</mat-option>
            </mat-select>
          </mat-form-field>
        </form>
        <div footer-actions>
          <button mat-flat-button color="primary" (click)="onSave()" [disabled]="saving()">
            {{ saving() ? 'Saving...' : (editingZone() ? 'Update Zone' : 'Create Zone') }}
          </button>
        </div>
      </app-detail-dialog>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .content-area { padding: 0 24px 24px; }
    .detail-grid { display: flex; flex-direction: column; }
    .detail-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--ops-border); }
    .detail-row:last-child { border-bottom: none; }
    .detail-label { font-size: 13px; color: var(--ops-text-muted); font-weight: 500; }
    .detail-value { font-size: 14px; color: var(--ops-text); text-align: right; }
    .mono { font-family: monospace; font-size: 13px; }
    .badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
    .badge.active { background: var(--ops-success-soft); color: var(--ops-success-strong); }
    .badge.inactive { background: var(--ops-item-hover); color: var(--ops-text-muted); }
    .form-body { display: flex; flex-direction: column; gap: 4px; }
    .full-width { width: 100%; }
    @media (max-width: 600px) { .content-area { padding: 0 12px 16px; } }
  `]
})
export class ZoneComponent implements OnInit {
  private masters = inject(MastersService);
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  zones = signal<Zone[]>([]);
  loading = signal(true);
  total = signal(0);
  pageIndex = signal(0);
  pageSize = 25;
  searchQuery = '';

  selectedZone = signal<Zone | null>(null);
  viewDialogOpen = signal(false);
  formDialogOpen = signal(false);
  editingZone = signal<Zone | null>(null);
  saving = signal(false);

  zoneTypes = ZONE_TYPES;
  get canManage() { return this.auth.hasPermission('masters.manage'); }

  columns: TableColumn[] = [
    { key: 'code', label: 'Code', sortable: true, width: '140px' },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'zone_type', label: 'Type', width: '140px' },
    {
      key: 'is_active', label: 'Status', type: 'badge', width: '100px',
      badgeConfig: {
        'true': { color: 'var(--ops-success-strong)', bg: 'var(--ops-success-soft)' },
        'false': { color: 'var(--ops-text-muted)', bg: 'var(--ops-item-hover)' }
      },
      format: (val) => val ? 'Active' : 'Inactive'
    }
  ];

  tableActions: TableAction[] = [
    { label: 'View', icon: 'visibility', color: 'primary' },
    { label: 'Edit', icon: 'edit', visible: () => this.canManage }
  ];

  form = this.fb.group({
    code: ['', Validators.required],
    name: ['', Validators.required],
    zone_type: ['']
  });

  ngOnInit(): void { this.loadZones(); }

  loadZones(): void {
    this.loading.set(true);
    this.masters.getZones({ page: this.pageIndex() + 1, size: this.pageSize }).subscribe({
      next: (res) => {
        if (Array.isArray(res)) { this.zones.set(res); this.total.set(res.length); }
        else { this.zones.set(res.items); this.total.set(res.total); }
        this.loading.set(false);
      },
      error: () => { this.snack.open('Failed to load zones', 'Dismiss', { duration: 3000 }); this.loading.set(false); }
    });
  }

  onView(zone: Zone): void { this.selectedZone.set(zone); this.viewDialogOpen.set(true); }

  openForm(zone?: Zone): void {
    this.editingZone.set(zone ?? null);
    if (zone) this.form.patchValue({ code: zone.code, name: zone.name, zone_type: zone.zone_type ?? '' });
    else this.form.reset();
    this.viewDialogOpen.set(false);
    this.formDialogOpen.set(true);
  }

  onTableAction(event: { action: string; row: unknown }): void {
    const zone = event.row as Zone;
    if (event.action === 'View') this.onView(zone);
    else if (event.action === 'Edit') this.openForm(zone);
  }

  onSave(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const obs = this.editingZone()
      ? this.masters.updateZone(this.editingZone()!.code, { name: val.name!, zone_type: val.zone_type ?? undefined })
      : this.masters.createZone({ code: val.code!, name: val.name!, zone_type: val.zone_type ?? undefined });
    obs.subscribe({
      next: () => {
        this.snack.open(`Zone ${this.editingZone() ? 'updated' : 'created'}`, 'Dismiss', { duration: 3000 });
        this.formDialogOpen.set(false);
        this.saving.set(false);
        this.loadZones();
      },
      error: () => { this.snack.open('Failed to save zone', 'Dismiss', { duration: 3000 }); this.saving.set(false); }
    });
  }

  onPage(event: { pageIndex: number }): void { this.pageIndex.set(event.pageIndex); this.loadZones(); }
  onSearch(query: string): void { this.searchQuery = query; this.pageIndex.set(0); this.loadZones(); }
}

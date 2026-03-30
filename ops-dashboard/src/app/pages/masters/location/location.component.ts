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
import { Location, Zone } from '../../../core/models/masters.model';

@Component({
  selector: 'app-location',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSnackBarModule,
    DataTableComponent, DetailDialogComponent, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="Locations" description="Manage warehouse storage locations" icon="location_on">
      </app-page-header>

      <div class="content-area">
        <app-data-table
          title="Locations"
          [columns]="columns"
          [dataSource]="locations()"
          [actions]="tableActions"
          [loading]="loading()"
          [totalItems]="total()"
          [pageSize]="pageSize"
          [pageIndex]="pageIndex()"
          [canCreate]="canManage"
          addLabel="Add Location"
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
        [title]="selectedLocation()?.name ?? ''"
        [subtitle]="selectedLocation()?.code"
        (closed)="viewDialogOpen.set(false)">
        <div header-actions>
          <button mat-icon-button color="primary" (click)="openForm(selectedLocation()!)" *ngIf="canManage">
            <mat-icon>edit</mat-icon>
          </button>
        </div>
        <div class="detail-grid" *ngIf="selectedLocation()">
          <div class="detail-row"><span class="detail-label">Code</span><span class="detail-value mono">{{ selectedLocation()!.code }}</span></div>
          <div class="detail-row"><span class="detail-label">Name</span><span class="detail-value">{{ selectedLocation()!.name }}</span></div>
          <div class="detail-row"><span class="detail-label">Zone</span><span class="detail-value">{{ selectedLocation()!.zone_name || selectedLocation()!.zone }}</span></div>
          <div class="detail-row"><span class="detail-label">Capacity</span><span class="detail-value">{{ selectedLocation()!.capacity ?? '—' }}</span></div>
          <div class="detail-row">
            <span class="detail-label">Status</span>
            <span class="badge" [class.active]="selectedLocation()!.is_active" [class.inactive]="!selectedLocation()!.is_active">
              {{ selectedLocation()!.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="detail-row"><span class="detail-label">Created</span><span class="detail-value">{{ selectedLocation()!.created_at | date:'dd MMM yyyy, HH:mm' }}</span></div>
        </div>
      </app-detail-dialog>

      <!-- Form dialog -->
      <app-detail-dialog
        [open]="formDialogOpen()"
        [title]="editingLocation() ? 'Edit Location' : 'New Location'"
        [showFooter]="true"
        (closed)="formDialogOpen.set(false)">
        <form [formGroup]="form" class="form-body">
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Location Code *</mat-label>
            <input matInput formControlName="code" placeholder="e.g. LOC-A01-01" [readonly]="!!editingLocation()">
            <mat-error>Required</mat-error>
          </mat-form-field>
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Name *</mat-label>
            <input matInput formControlName="name" placeholder="Location name">
            <mat-error>Required</mat-error>
          </mat-form-field>
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Zone *</mat-label>
            <mat-select formControlName="zone">
              <mat-option *ngFor="let z of zones()" [value]="z.code">{{ z.name }} ({{ z.code }})</mat-option>
            </mat-select>
            <mat-error>Required</mat-error>
          </mat-form-field>
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Capacity</mat-label>
            <input matInput type="number" formControlName="capacity" placeholder="Optional">
          </mat-form-field>
        </form>
        <div footer-actions>
          <button mat-flat-button color="primary" (click)="onSave()" [disabled]="saving()">
            {{ saving() ? 'Saving...' : (editingLocation() ? 'Update Location' : 'Create Location') }}
          </button>
        </div>
      </app-detail-dialog>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .content-area { padding: 0 24px 24px; }
    .detail-grid { display: flex; flex-direction: column; }
    .detail-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
    .detail-row:last-child { border-bottom: none; }
    .detail-label { font-size: 13px; color: #64748b; font-weight: 500; }
    .detail-value { font-size: 14px; color: #1e293b; }
    .mono { font-family: monospace; font-size: 13px; }
    .badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
    .badge.active { background: #dcfce7; color: #16a34a; }
    .badge.inactive { background: #f1f5f9; color: #64748b; }
    .form-body { display: flex; flex-direction: column; gap: 4px; }
    .full-width { width: 100%; }
    @media (max-width: 600px) { .content-area { padding: 0 12px 16px; } }
  `]
})
export class LocationComponent implements OnInit {
  private masters = inject(MastersService);
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  locations = signal<Location[]>([]);
  zones = signal<Zone[]>([]);
  loading = signal(true);
  total = signal(0);
  pageIndex = signal(0);
  pageSize = 25;

  selectedLocation = signal<Location | null>(null);
  viewDialogOpen = signal(false);
  formDialogOpen = signal(false);
  editingLocation = signal<Location | null>(null);
  saving = signal(false);

  get canManage() { return this.auth.hasPermission('masters.manage'); }

  columns: TableColumn[] = [
    { key: 'code', label: 'Code', sortable: true, width: '150px' },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'zone_name', label: 'Zone' },
    { key: 'capacity', label: 'Capacity', type: 'number', width: '100px' },
    {
      key: 'is_active', label: 'Status', type: 'badge', width: '100px',
      badgeConfig: {
        'true': { color: '#16a34a', bg: '#dcfce7' },
        'false': { color: '#64748b', bg: '#f1f5f9' }
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
    zone: ['', Validators.required],
    capacity: [null as number | null]
  });

  ngOnInit(): void {
    this.loadLocations();
    this.loadZones();
  }

  loadLocations(): void {
    this.loading.set(true);
    this.masters.getLocations({ page: this.pageIndex() + 1, size: this.pageSize }).subscribe({
      next: (res) => {
        if (Array.isArray(res)) { this.locations.set(res); this.total.set(res.length); }
        else { this.locations.set(res.items); this.total.set(res.total); }
        this.loading.set(false);
      },
      error: () => { this.snack.open('Failed to load locations', 'Dismiss', { duration: 3000 }); this.loading.set(false); }
    });
  }

  loadZones(): void {
    this.masters.getZones({ size: 200 }).subscribe({
      next: (res) => {
        this.zones.set(Array.isArray(res) ? res : res.items);
      }
    });
  }

  onView(loc: Location): void { this.selectedLocation.set(loc); this.viewDialogOpen.set(true); }

  openForm(loc?: Location): void {
    this.editingLocation.set(loc ?? null);
    if (loc) this.form.patchValue({ code: loc.code, name: loc.name, zone: loc.zone, capacity: loc.capacity ?? null });
    else this.form.reset();
    this.viewDialogOpen.set(false);
    this.formDialogOpen.set(true);
  }

  onTableAction(event: { action: string; row: unknown }): void {
    const loc = event.row as Location;
    if (event.action === 'View') this.onView(loc);
    else if (event.action === 'Edit') this.openForm(loc);
  }

  onSave(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const obs = this.editingLocation()
      ? this.masters.updateLocation(this.editingLocation()!.code, { name: val.name!, zone: val.zone!, capacity: val.capacity ?? undefined })
      : this.masters.createLocation({ code: val.code!, name: val.name!, zone: val.zone!, capacity: val.capacity ?? undefined });
    obs.subscribe({
      next: () => {
        this.snack.open(`Location ${this.editingLocation() ? 'updated' : 'created'}`, 'Dismiss', { duration: 3000 });
        this.formDialogOpen.set(false);
        this.saving.set(false);
        this.loadLocations();
      },
      error: () => { this.snack.open('Failed to save location', 'Dismiss', { duration: 3000 }); this.saving.set(false); }
    });
  }

  onPage(event: { pageIndex: number }): void { this.pageIndex.set(event.pageIndex); this.loadLocations(); }
  onSearch(_query: string): void { this.pageIndex.set(0); this.loadLocations(); }
}

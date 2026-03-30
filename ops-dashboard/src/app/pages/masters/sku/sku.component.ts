import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { DataTableComponent, TableColumn, TableAction } from '../../../shared/components/data-table/data-table.component';
import { DetailDialogComponent } from '../../../shared/components/detail-dialog/detail-dialog.component';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { MastersService } from '../../../core/services/masters.service';
import { AuthService } from '../../../core/auth/auth.service';
import { Sku } from '../../../core/models/masters.model';

const UOM_OPTIONS = ['EA', 'KG', 'G', 'L', 'ML', 'BOX', 'CASE', 'PALLET', 'ROLL', 'BAG', 'PIECE'];

@Component({
  selector: 'app-sku',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSlideToggleModule,
    MatSnackBarModule, MatDialogModule,
    DataTableComponent, DetailDialogComponent,
    ConfirmDialogComponent, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="SKUs" description="Manage stock-keeping units" icon="inventory_2">
      </app-page-header>

      <div class="content-area">
        <app-data-table
          title="SKUs"
          [columns]="columns"
          [dataSource]="skus()"
          [actions]="tableActions"
          [loading]="loading()"
          [totalItems]="total()"
          [pageSize]="pageSize"
          [pageIndex]="pageIndex()"
          [canCreate]="canManage"
          addLabel="Add SKU"
          (rowClick)="onView($any($event))"
          (actionClick)="onTableAction($event)"
          (addClick)="openForm()"
          (pageChange)="onPage($event)"
          (search)="onSearch($event)">
        </app-data-table>
      </div>

      <!-- Detail / View dialog -->
      <app-detail-dialog
        [open]="viewDialogOpen()"
        [title]="selectedSku()?.name ?? ''"
        [subtitle]="selectedSku()?.code"
        (closed)="viewDialogOpen.set(false)">
        <div header-actions>
          <button mat-icon-button color="primary" (click)="openForm(selectedSku()!)" *ngIf="canManage">
            <mat-icon>edit</mat-icon>
          </button>
        </div>

        <div class="detail-grid" *ngIf="selectedSku()">
          <div class="detail-row">
            <span class="detail-label">Code</span>
            <span class="detail-value mono">{{ selectedSku()!.code }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Name</span>
            <span class="detail-value">{{ selectedSku()!.name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Description</span>
            <span class="detail-value">{{ selectedSku()!.description || '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Unit of Measure</span>
            <span class="detail-value">{{ selectedSku()!.uom }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Status</span>
            <span class="badge" [class.active]="selectedSku()!.is_active" [class.inactive]="!selectedSku()!.is_active">
              {{ selectedSku()!.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Created</span>
            <span class="detail-value">{{ selectedSku()!.created_at | date:'dd MMM yyyy, HH:mm' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Updated</span>
            <span class="detail-value">{{ selectedSku()!.updated_at | date:'dd MMM yyyy, HH:mm' }}</span>
          </div>
        </div>
      </app-detail-dialog>

      <!-- Create / Edit form dialog -->
      <app-detail-dialog
        [open]="formDialogOpen()"
        [title]="editingSku() ? 'Edit SKU' : 'New SKU'"
        [showFooter]="true"
        (closed)="formDialogOpen.set(false)">

        <form [formGroup]="form" class="form-body">
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>SKU Code *</mat-label>
            <input matInput formControlName="code" placeholder="e.g. SKU-001"
                   [readonly]="!!editingSku()" style="text-transform:uppercase">
            <mat-error>Required</mat-error>
          </mat-form-field>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Name *</mat-label>
            <input matInput formControlName="name" placeholder="Product name">
            <mat-error>Required</mat-error>
          </mat-form-field>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Description</mat-label>
            <textarea matInput formControlName="description" rows="3"
                      placeholder="Optional description"></textarea>
          </mat-form-field>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Unit of Measure *</mat-label>
            <mat-select formControlName="uom">
              <mat-option *ngFor="let u of uomOptions" [value]="u">{{ u }}</mat-option>
            </mat-select>
            <mat-error>Required</mat-error>
          </mat-form-field>
        </form>

        <div footer-actions>
          <button mat-flat-button color="primary" (click)="onSave()" [disabled]="saving()">
            {{ saving() ? 'Saving...' : (editingSku() ? 'Update SKU' : 'Create SKU') }}
          </button>
        </div>
      </app-detail-dialog>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .content-area { padding: 0 24px 24px; }
    .detail-grid { display: flex; flex-direction: column; gap: 0; }
    .detail-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #f1f5f9;
    }
    .detail-row:last-child { border-bottom: none; }
    .detail-label { font-size: 13px; color: #64748b; font-weight: 500; }
    .detail-value { font-size: 14px; color: #1e293b; }
    .mono { font-family: monospace; font-size: 13px; }
    .badge {
      font-size: 12px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 20px;
    }
    .badge.active { background: #dcfce7; color: #16a34a; }
    .badge.inactive { background: #f1f5f9; color: #64748b; }
    .form-body { display: flex; flex-direction: column; gap: 4px; }
    .full-width { width: 100%; }

    @media (max-width: 600px) {
      .content-area { padding: 0 12px 16px; }
    }
  `]
})
export class SkuComponent implements OnInit {
  private masters = inject(MastersService);
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  skus = signal<Sku[]>([]);
  loading = signal(true);
  total = signal(0);
  pageIndex = signal(0);
  pageSize = 25;
  searchQuery = '';

  selectedSku = signal<Sku | null>(null);
  viewDialogOpen = signal(false);
  formDialogOpen = signal(false);
  editingSku = signal<Sku | null>(null);
  saving = signal(false);

  uomOptions = UOM_OPTIONS;

  form = this.fb.group({
    code: ['', Validators.required],
    name: ['', Validators.required],
    description: [''],
    uom: ['EA', Validators.required]
  });

  get canManage() { return this.auth.hasPermission('masters.manage'); }

  columns: TableColumn[] = [
    { key: 'code', label: 'Code', sortable: true, width: '140px' },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'uom', label: 'UOM', width: '80px' },
    { key: 'description', label: 'Description' },
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

  ngOnInit(): void {
    this.loadSkus();
  }

  loadSkus(): void {
    this.loading.set(true);
    this.masters.getSkus({
      page: this.pageIndex() + 1,
      size: this.pageSize,
      ...(this.searchQuery ? { search: this.searchQuery } : {})
    }).subscribe({
      next: (res) => {
        if (Array.isArray(res)) {
          this.skus.set(res);
          this.total.set(res.length);
        } else {
          this.skus.set(res.items);
          this.total.set(res.total);
        }
        this.loading.set(false);
      },
      error: () => {
        this.snack.open('Failed to load SKUs', 'Dismiss', { duration: 3000 });
        this.loading.set(false);
      }
    });
  }

  onView(sku: Sku): void {
    this.selectedSku.set(sku);
    this.viewDialogOpen.set(true);
  }

  openForm(sku?: Sku): void {
    this.editingSku.set(sku ?? null);
    if (sku) {
      this.form.patchValue({ code: sku.code, name: sku.name, description: sku.description ?? '', uom: sku.uom });
      this.form.get('code')?.disable();
    } else {
      this.form.reset({ uom: 'EA' });
      this.form.get('code')?.enable();
    }
    this.viewDialogOpen.set(false);
    this.formDialogOpen.set(true);
  }

  onTableAction(event: { action: string; row: unknown }): void {
    const sku = event.row as Sku;
    if (event.action === 'View') this.onView(sku);
    else if (event.action === 'Edit') this.openForm(sku);
  }

  onSave(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.saving.set(true);
    const val = this.form.getRawValue();
    const obs = this.editingSku()
      ? this.masters.updateSku(this.editingSku()!.code, { name: val.name!, description: val.description ?? undefined, uom: val.uom! })
      : this.masters.createSku({ code: val.code!, name: val.name!, description: val.description ?? undefined, uom: val.uom! });

    obs.subscribe({
      next: () => {
        this.snack.open(`SKU ${this.editingSku() ? 'updated' : 'created'} successfully`, 'Dismiss', { duration: 3000 });
        this.formDialogOpen.set(false);
        this.saving.set(false);
        this.loadSkus();
      },
      error: () => {
        this.snack.open('Failed to save SKU', 'Dismiss', { duration: 3000 });
        this.saving.set(false);
      }
    });
  }

  onPage(event: { pageIndex: number }): void {
    this.pageIndex.set(event.pageIndex);
    this.loadSkus();
  }

  onSearch(query: string): void {
    this.searchQuery = query;
    this.pageIndex.set(0);
    this.loadSkus();
  }
}

import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { DataTableComponent, TableColumn, TableAction } from '../../../shared/components/data-table/data-table.component';
import { DetailDialogComponent } from '../../../shared/components/detail-dialog/detail-dialog.component';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../../core/services/operations.service';
import { AuthService } from '../../../core/auth/auth.service';
import { Transaction, TransactionListItem, TransactionType, TransactionStatus } from '../../../core/models/operations.model';

const STATUS_BADGE: Record<string, { color: string; bg: string }> = {
  PENDING:     { color: 'var(--ops-warning-strong)', bg: 'var(--ops-warning-soft)' },
  IN_PROGRESS: { color: 'var(--ops-primary)', bg: 'var(--ops-primary-soft)' },
  COMPLETED:   { color: 'var(--ops-success-strong)', bg: 'var(--ops-success-soft)' },
  FAILED:      { color: 'var(--ops-danger-strong)', bg: 'var(--ops-danger-soft)' },
  CANCELLED:   { color: 'var(--ops-text-muted)', bg: 'var(--ops-item-hover)' }
};

@Component({
  selector: 'app-transactions-list',
  standalone: true,
  imports: [
    CommonModule, RouterModule, FormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSnackBarModule,
    MatDialogModule, MatDividerModule, MatTooltipModule,
    DataTableComponent, DetailDialogComponent,
    ConfirmDialogComponent, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="Transactions" description="View and manage all WMS transactions" icon="receipt_long">
      </app-page-header>

      <!-- Type filter -->
      <div class="filters">
        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>Type</mat-label>
          <mat-select [(ngModel)]="typeFilter" (selectionChange)="applyFilter()">
            <mat-option value="">All Types</mat-option>
            <mat-option *ngFor="let t of txnTypes" [value]="t">{{ t }}</mat-option>
          </mat-select>
        </mat-form-field>
        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>Status</mat-label>
          <mat-select [(ngModel)]="statusFilter" (selectionChange)="applyFilter()">
            <mat-option value="">All Statuses</mat-option>
            <mat-option *ngFor="let s of txnStatuses" [value]="s">{{ s }}</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      <div class="content-area">
        <app-data-table
          title="Transactions"
          [columns]="columns"
          [dataSource]="transactions()"
          [actions]="tableActions"
          [loading]="loading()"
          [totalItems]="total()"
          [pageSize]="pageSize"
          [pageIndex]="pageIndex()"
          [canCreate]="false"
          (rowClick)="onView($any($event))"
          (actionClick)="onTableAction($event)"
          (pageChange)="onPage($event)"
          (search)="onSearch($event)">
        </app-data-table>
      </div>

      <!-- Transaction detail dialog -->
      <app-detail-dialog
        [open]="viewDialogOpen()"
        [title]="selectedTxn()?.type ?? 'Transaction'"
        [subtitle]="selectedTxn()?.reference ?? selectedTxn()?.id?.slice(0,8) ?? ''"
        (closed)="closeDetailDialog()">

        <div header-actions *ngIf="selectedTxn()">
          <button mat-icon-button color="primary"
                  *ngIf="selectedTxn()!.status === 'PENDING' && canExecute"
                  (click)="onExecute(selectedTxn()!)"
                  matTooltip="Execute Transaction">
            <mat-icon>play_arrow</mat-icon>
          </button>
          <button mat-icon-button color="warn"
                  *ngIf="selectedTxn()!.status === 'PENDING' && canManage"
                  (click)="onCancel(selectedTxn()!)"
                  matTooltip="Cancel Transaction">
            <mat-icon>cancel</mat-icon>
          </button>
        </div>

        <div class="txn-detail" *ngIf="selectedTxn() && !loadingDetail()">
          <!-- Header info -->
          <div class="detail-grid">
            <div class="detail-row"><span class="detail-label">ID</span><span class="detail-value mono small">{{ selectedTxn()!.id }}</span></div>
            <div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">{{ selectedTxn()!.type }}</span></div>
            <div class="detail-row">
              <span class="detail-label">Status</span>
              <span class="badge" [style.color]="statusBadge(selectedTxn()!.status).color" [style.background]="statusBadge(selectedTxn()!.status).bg">
                {{ selectedTxn()!.status }}
              </span>
            </div>
            <div class="detail-row"><span class="detail-label">Reference</span><span class="detail-value">{{ selectedTxn()!.reference || '—' }}</span></div>
            <div class="detail-row"><span class="detail-label">Notes</span><span class="detail-value">{{ selectedTxn()!.notes || '—' }}</span></div>
            <div class="detail-row"><span class="detail-label">Created</span><span class="detail-value">{{ selectedTxn()!.created_at | date:'dd MMM yyyy, HH:mm' }}</span></div>
            <div class="detail-row" *ngIf="selectedTxn()!.executed_at">
              <span class="detail-label">Executed</span>
              <span class="detail-value">{{ selectedTxn()!.executed_at | date:'dd MMM yyyy, HH:mm' }}</span>
            </div>
          </div>

          <!-- Picks -->
          <div class="txn-section" *ngIf="selectedTxn()!.picks?.length">
            <div class="section-label">Picks ({{ selectedTxn()!.picks.length }})</div>
            <div class="line-item" *ngFor="let pick of selectedTxn()!.picks">
              <div class="line-main">
                <span class="sku-code">{{ pick.sku_code }}</span>
                <span class="qty-badge">× {{ pick.quantity }}</span>
              </div>
              <div class="line-sub">{{ pick.source_type }}: {{ pick.source_code }}</div>
              <span class="task-status" [class]="'ts-' + pick.status.toLowerCase()">{{ pick.status }}</span>
            </div>
          </div>

          <!-- Drops -->
          <div class="txn-section" *ngIf="selectedTxn()!.drops?.length">
            <div class="section-label">Drops ({{ selectedTxn()!.drops.length }})</div>
            <div class="line-item" *ngFor="let drop of selectedTxn()!.drops">
              <div class="line-main">
                <span class="sku-code">{{ drop.sku_code }}</span>
                <span class="qty-badge">× {{ drop.quantity }}</span>
              </div>
              <div class="line-sub">{{ drop.destination_type }}: {{ drop.destination_code }}</div>
              <span class="task-status" [class]="'ts-' + drop.status.toLowerCase()">{{ drop.status }}</span>
            </div>
          </div>

          <!-- Document link -->
          <div class="doc-link" *ngIf="selectedTxn()!.document_url">
            <a [href]="selectedTxn()!.document_url" target="_blank" mat-stroked-button>
              <mat-icon>picture_as_pdf</mat-icon>
              View Document
            </a>
          </div>
        </div>

        <div class="loading-detail" *ngIf="loadingDetail()">
          Loading details...
        </div>
      </app-detail-dialog>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .filters {
      display: flex;
      gap: 12px;
      padding: 0 24px 12px;
      flex-wrap: wrap;
    }
    .filter-field { min-width: 160px; }
    .filter-field ::ng-deep .mat-mdc-form-field-subscript-wrapper { display: none; }
    .content-area { padding: 0 24px 24px; }
    .txn-detail { }
    .detail-grid { display: flex; flex-direction: column; margin-bottom: 16px; }
    .detail-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 10px 0; border-bottom: 1px solid var(--ops-border); }
    .detail-row:last-child { border-bottom: none; }
    .detail-label { font-size: 13px; color: var(--ops-text-muted); font-weight: 500; }
    .detail-value { font-size: 14px; color: var(--ops-text); text-align: right; }
    .mono { font-family: monospace; }
    .small { font-size: 12px; }
    .badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
    .txn-section { margin-bottom: 16px; }
    .section-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ops-text-soft); margin-bottom: 8px; }
    .line-item {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      padding: 10px 12px;
      background: var(--ops-item-hover);
      border: 1px solid var(--ops-border);
      border-radius: 8px;
      margin-bottom: 6px;
    }
    .line-main { display: flex; align-items: center; gap: 8px; flex: 1; }
    .sku-code { font-weight: 600; font-size: 14px; color: var(--ops-text); font-family: monospace; }
    .qty-badge { background: var(--ops-primary-soft); color: var(--ops-primary); font-weight: 600; font-size: 13px; padding: 1px 8px; border-radius: 12px; }
    .line-sub { font-size: 12px; color: var(--ops-text-muted); flex: 1; min-width: 180px; }
    .task-status { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 12px; }
    .ts-pending { background: var(--ops-warning-soft); color: var(--ops-warning-strong); }
    .ts-completed { background: var(--ops-success-soft); color: var(--ops-success-strong); }
    .ts-in_progress { background: var(--ops-primary-soft); color: var(--ops-primary); }
    .ts-cancelled { background: var(--ops-item-hover); color: var(--ops-text-muted); border: 1px solid var(--ops-border); }
    .doc-link { margin-top: 16px; }
    .loading-detail { padding: 24px; text-align: center; color: var(--ops-text-muted); }
    @media (max-width: 600px) { .content-area { padding: 0 12px 16px; } .filters { padding: 0 12px 12px; } }
  `]
})
export class TransactionsListComponent implements OnInit {
  private ops = inject(OperationsService);
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private dialog = inject(MatDialog);

  transactions = signal<TransactionListItem[]>([]);
  loading = signal(true);
  total = signal(0);
  pageIndex = signal(0);
  pageSize = 25;
  searchQuery = '';
  typeFilter: TransactionType | '' = '';
  statusFilter: TransactionStatus | '' = '';

  selectedTxn = signal<Transaction | null>(null);
  viewDialogOpen = signal(false);
  loadingDetail = signal(false);
  private lastDialogCloseAt = 0;

  txnTypes: TransactionType[] = ['GRN', 'MOVE', 'PUTAWAY', 'ORDER_PICK', 'RETURN', 'CYCLE_COUNT', 'ADJUSTMENT'];
  txnStatuses: TransactionStatus[] = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED'];

  get canManage() { return this.auth.hasPermission('transactions.manage'); }
  get canExecute() { return this.auth.hasPermission('operations.execute'); }

  statusBadge(status: string) {
    return STATUS_BADGE[status] ?? { color: 'var(--ops-text-muted)', bg: 'var(--ops-item-hover)' };
  }

  columns: TableColumn[] = [
    { key: 'type', label: 'Type', width: '120px', type: 'badge',
      badgeConfig: {
        GRN: { color: 'var(--ops-success-strong)', bg: 'var(--ops-success-soft)' },
        MOVE: { color: 'var(--ops-warning-strong)', bg: 'var(--ops-warning-soft)' },
        PUTAWAY: { color: 'var(--ops-accent-violet)', bg: 'var(--ops-accent-violet-soft)' },
        ORDER_PICK: { color: 'var(--ops-danger-strong)', bg: 'var(--ops-danger-soft)' },
        RETURN: { color: 'var(--ops-primary)', bg: 'var(--ops-primary-soft)' },
        CYCLE_COUNT: { color: 'var(--ops-text-muted)', bg: 'var(--ops-item-hover)' },
        ADJUSTMENT: { color: 'var(--ops-text-muted)', bg: 'var(--ops-item-hover)' }
      }
    },
    { key: 'status', label: 'Status', type: 'badge', width: '130px',
      badgeConfig: STATUS_BADGE
    },
    { key: 'reference', label: 'Reference', format: (v) => v as string || '—' },
    { key: 'created_at', label: 'Created', type: 'date', sortable: true }
  ];

  tableActions: TableAction[] = [
    { label: 'View', icon: 'visibility', color: 'primary' },
    {
      label: 'Execute', icon: 'play_arrow', color: 'primary',
      visible: (row) => (row as TransactionListItem).status === 'PENDING' && this.canExecute
    }
  ];

  ngOnInit(): void { this.loadTransactions(); }

  loadTransactions(): void {
    this.loading.set(true);
    this.ops.getTransactions({
      page: this.pageIndex() + 1,
      size: this.pageSize,
      ...(this.typeFilter ? { transaction_type: this.typeFilter } : {}),
      ...(this.statusFilter ? { status: this.statusFilter } : {})
    }).subscribe({
      next: (res) => {
        if (Array.isArray(res)) { this.transactions.set(res); this.total.set(res.length); }
        else { this.transactions.set(res.items); this.total.set(res.total); }
        this.loading.set(false);
      },
      error: () => { this.snack.open('Failed to load transactions', 'Dismiss', { duration: 3000 }); this.loading.set(false); }
    });
  }

  onView(txn: TransactionListItem): void {
    if (performance.now() - this.lastDialogCloseAt < 250) return;
    this.viewDialogOpen.set(true);
    this.loadingDetail.set(true);
    this.ops.getTransaction(txn.id).subscribe({
      next: (detail) => { this.selectedTxn.set(detail); this.loadingDetail.set(false); },
      error: () => { this.loadingDetail.set(false); }
    });
  }

  onTableAction(event: { action: string; row: unknown }): void {
    const txn = event.row as TransactionListItem;
    if (event.action === 'View') this.onView(txn);
    else if (event.action === 'Execute') this.executeById(txn.id);
  }

  onExecute(txn: Transaction): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: { title: 'Execute Transaction', message: `Execute this ${txn.type} transaction? Inventory will be updated.`, confirmLabel: 'Execute' }
    });
    ref.afterClosed().subscribe(confirmed => {
      if (confirmed) this.executeById(txn.id);
    });
  }

  executeById(id: string): void {
    this.ops.executeTransaction(id).subscribe({
      next: (updated) => {
        this.snack.open('Transaction executed successfully', 'Dismiss', { duration: 3000 });
        this.selectedTxn.set(updated);
        this.loadTransactions();
      },
      error: () => this.snack.open('Failed to execute transaction', 'Dismiss', { duration: 3000 })
    });
  }

  onCancel(txn: Transaction): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: { title: 'Cancel Transaction', message: 'Cancel this transaction?', confirmLabel: 'Cancel', danger: true }
    });
    ref.afterClosed().subscribe(confirmed => {
      if (confirmed) {
        this.ops.cancelTransaction(txn.id).subscribe({
          next: (updated) => {
            this.snack.open('Transaction cancelled', 'Dismiss', { duration: 3000 });
            this.selectedTxn.set(updated);
            this.loadTransactions();
          },
          error: () => this.snack.open('Failed to cancel', 'Dismiss', { duration: 3000 })
        });
      }
    });
  }

  applyFilter(): void { this.pageIndex.set(0); this.loadTransactions(); }
  onPage(event: { pageIndex: number; pageSize: number }): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize = event.pageSize;
    this.loadTransactions();
  }
  onSearch(_q: string): void { this.pageIndex.set(0); this.loadTransactions(); }

  closeDetailDialog(): void {
    this.lastDialogCloseAt = performance.now();
    this.viewDialogOpen.set(false);
    this.loadingDetail.set(false);
    this.selectedTxn.set(null);
  }
}

import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DataTableComponent, TableColumn } from '../../shared/components/data-table/data-table.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../core/services/operations.service';
import { InventoryBalance } from '../../core/models/operations.model';

@Component({
  selector: 'app-inventory',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSnackBarModule,
    DataTableComponent, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="Stock Balances" description="Real-time inventory across all locations" icon="inventory">
      </app-page-header>

      <div class="content-area">
        <app-data-table
          title="Balances"
          [columns]="columns"
          [dataSource]="balances()"
          [loading]="loading()"
          [totalItems]="total()"
          [pageSize]="pageSize"
          [pageIndex]="pageIndex()"
          [canCreate]="false"
          [actions]="[]"
          (pageChange)="onPage($event)"
          (search)="onSearch($event)">
        </app-data-table>
      </div>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .content-area { padding: 0 24px 24px; }
    @media (max-width: 600px) { .content-area { padding: 0 12px 16px; } }
  `]
})
export class InventoryComponent implements OnInit {
  private ops = inject(OperationsService);
  private snack = inject(MatSnackBar);

  balances = signal<InventoryBalance[]>([]);
  loading = signal(true);
  total = signal(0);
  pageIndex = signal(0);
  pageSize = 50;

  columns: TableColumn[] = [
    { key: 'sku_code', label: 'SKU', sortable: true, width: '140px' },
    { key: 'sku_name', label: 'SKU Name' },
    { key: 'entity_type', label: 'Location Type', width: '130px' },
    { key: 'entity_code', label: 'Location Code', width: '150px' },
    { key: 'on_hand', label: 'On Hand', type: 'number', width: '100px', sortable: true },
    { key: 'reserved', label: 'Reserved', type: 'number', width: '100px' },
    { key: 'available', label: 'Available', type: 'number', width: '100px', sortable: true },
    { key: 'batch', label: 'Batch', width: '120px', format: (v) => (v as string) || '—' }
  ];

  ngOnInit(): void { this.loadBalances(); }

  loadBalances(): void {
    this.loading.set(true);
    this.ops.getBalances({ page: this.pageIndex() + 1, size: this.pageSize }).subscribe({
      next: (res) => {
        if (Array.isArray(res)) { this.balances.set(res); this.total.set(res.length); }
        else { this.balances.set(res.items); this.total.set(res.total); }
        this.loading.set(false);
      },
      error: () => { this.snack.open('Failed to load inventory', 'Dismiss', { duration: 3000 }); this.loading.set(false); }
    });
  }

  onPage(event: { pageIndex: number }): void { this.pageIndex.set(event.pageIndex); this.loadBalances(); }
  onSearch(_q: string): void { this.pageIndex.set(0); this.loadBalances(); }
}

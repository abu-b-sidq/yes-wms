import {
  Component, Input, Output, EventEmitter, OnChanges,
  SimpleChanges, TemplateRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  type?: 'text' | 'date' | 'badge' | 'number' | 'custom';
  badgeConfig?: Record<string, { color: string; bg: string }>;
  format?: (value: unknown, row: unknown) => string;
}

export interface TableAction {
  label: string;
  icon: string;
  color?: 'primary' | 'accent' | 'warn';
  permission?: string;
  disabled?: (row: unknown) => boolean;
  visible?: (row: unknown) => boolean;
}

@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatTableModule, MatSortModule, MatPaginatorModule,
    MatInputModule, MatFormFieldModule, MatIconModule,
    MatButtonModule, MatProgressSpinnerModule, MatChipsModule,
    MatTooltipModule, MatMenuModule
  ],
  template: `
    <div class="data-table-container">
      <!-- Toolbar -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <mat-form-field appearance="outline" class="search-field" *ngIf="searchable">
            <mat-label>Search</mat-label>
            <mat-icon matPrefix>search</mat-icon>
            <input matInput [(ngModel)]="searchQuery" (input)="onSearch()" [placeholder]="'Search ' + title.toLowerCase()">
            <button mat-icon-button matSuffix *ngIf="searchQuery" (click)="clearSearch()">
              <mat-icon>close</mat-icon>
            </button>
          </mat-form-field>
        </div>
        <div class="toolbar-right">
          <ng-content select="[toolbar-actions]"></ng-content>
          <button mat-flat-button color="primary" *ngIf="canCreate" (click)="onAdd()">
            <mat-icon>add</mat-icon>
            {{ addLabel }}
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="table-wrapper">
        <!-- Loading -->
        <div class="loading-overlay" *ngIf="loading">
          <mat-spinner diameter="40"></mat-spinner>
        </div>

        <!-- Empty state -->
        <div class="empty-state" *ngIf="!loading && dataSource.length === 0">
          <mat-icon class="empty-icon">inbox</mat-icon>
          <p>No {{ title.toLowerCase() }} found</p>
          <button mat-stroked-button color="primary" *ngIf="canCreate" (click)="onAdd()">
            <mat-icon>add</mat-icon> Add {{ title }}
          </button>
        </div>

        <table mat-table [dataSource]="dataSource" matSort (matSortChange)="onSort($event)"
               class="data-table" *ngIf="dataSource.length > 0 || loading">

          <!-- Dynamic columns -->
          <ng-container *ngFor="let col of columns" [matColumnDef]="col.key">
            <th mat-header-cell *matHeaderCellDef [mat-sort-header]="col.sortable ? col.key : ''"
                [style.width]="col.width">
              {{ col.label }}
            </th>
            <td mat-cell *matCellDef="let row" (click)="onRowClick(row)" class="clickable-cell">
              <!-- Badge type -->
              <ng-container *ngIf="col.type === 'badge'">
                <span class="badge"
                      [style.color]="col.badgeConfig?.[$any(getCellValue(row, col.key))]?.color ?? 'var(--ops-text-muted)'"
                      [style.background]="col.badgeConfig?.[$any(getCellValue(row, col.key))]?.bg ?? 'var(--ops-item-active)'">
                  {{ getCellValue(row, col.key) }}
                </span>
              </ng-container>
              <!-- Date type -->
              <ng-container *ngIf="col.type === 'date'">
                {{ $any(getCellValue(row, col.key)) | date:'dd MMM yyyy, HH:mm' }}
              </ng-container>
              <!-- Number type -->
              <ng-container *ngIf="col.type === 'number'">
                {{ $any(getCellValue(row, col.key)) | number }}
              </ng-container>
              <!-- Custom format -->
              <ng-container *ngIf="col.type === 'custom' && col.format">
                {{ col.format(getCellValue(row, col.key), row) }}
              </ng-container>
              <!-- Default text -->
              <ng-container *ngIf="!col.type || col.type === 'text'">
                {{ getCellValue(row, col.key) }}
              </ng-container>
            </td>
          </ng-container>

          <!-- Actions column -->
          <ng-container matColumnDef="actions" *ngIf="actions.length > 0">
            <th mat-header-cell *matHeaderCellDef class="actions-header">Actions</th>
            <td mat-cell *matCellDef="let row" class="actions-cell" (click)="$event.stopPropagation()">
              <ng-container *ngFor="let action of actions">
                <button mat-icon-button
                        *ngIf="!action.visible || action.visible(row)"
                        [disabled]="action.disabled ? action.disabled(row) : false"
                        [color]="action.color"
                        [matTooltip]="action.label"
                        (click)="onAction(action.label, row)">
                  <mat-icon>{{ action.icon }}</mat-icon>
                </button>
              </ng-container>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns; sticky: true"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"
              class="table-row" (click)="onRowClick(row)"></tr>
        </table>
      </div>

      <!-- Paginator -->
      <mat-paginator
        *ngIf="paginated"
        [length]="totalItems"
        [pageSize]="pageSize"
        [pageIndex]="pageIndex"
        [pageSizeOptions]="[10, 25, 50, 100]"
        (page)="onPage($event)"
        showFirstLastButtons>
      </mat-paginator>
    </div>
  `,
  styles: [`
    .data-table-container {
      background: var(--ops-elevated-bg);
      border: 1px solid var(--ops-border);
      border-radius: 18px;
      box-shadow: var(--ops-shadow);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .table-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 16px 0;
      gap: 16px;
      flex-wrap: wrap;
    }
    .toolbar-left { display: flex; gap: 8px; flex: 1; }
    .toolbar-right { display: flex; gap: 8px; align-items: center; }
    .search-field {
      min-width: 240px;
      max-width: 400px;
    }
    .search-field ::ng-deep .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }
    .table-wrapper {
      position: relative;
      overflow-x: auto;
      min-height: 200px;
    }
    .loading-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--ops-glass);
      z-index: 5;
    }
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px 24px;
      gap: 8px;
      color: var(--ops-text-soft);
    }
    .empty-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: var(--ops-muted-strong);
    }
    .empty-state p {
      font-size: 15px;
      margin: 0;
    }
    .data-table {
      width: 100%;
    }
    .table-row {
      cursor: pointer;
      transition: background 0.1s;
    }
    .table-row:hover {
      background: var(--ops-row-hover) !important;
    }
    .clickable-cell {
      font-size: 14px;
      color: var(--ops-text);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
    }
    .actions-header { width: 120px; text-align: center; }
    .actions-cell { text-align: center; white-space: nowrap; }
    ::ng-deep .mat-mdc-header-cell {
      font-weight: 600 !important;
      font-size: 12px !important;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--ops-text-soft) !important;
      background: var(--ops-item-hover);
    }
    ::ng-deep .mat-mdc-cell {
      border-bottom-color: var(--ops-border) !important;
      color: var(--ops-text);
    }
    ::ng-deep .mat-mdc-paginator-container {
      border-top: 1px solid var(--ops-border);
    }
    ::ng-deep .mat-mdc-row:last-child td {
      border-bottom: none;
    }

    @media (max-width: 600px) {
      .table-toolbar {
        flex-direction: column;
        align-items: stretch;
      }
      .search-field {
        min-width: unset;
        max-width: unset;
        width: 100%;
      }
    }
  `]
})
export class DataTableComponent implements OnChanges {
  @Input() title = 'Items';
  @Input() columns: TableColumn[] = [];
  @Input() dataSource: unknown[] = [];
  @Input() actions: TableAction[] = [];
  @Input() loading = false;
  @Input() paginated = true;
  @Input() totalItems = 0;
  @Input() pageSize = 25;
  @Input() pageIndex = 0;
  @Input() searchable = true;
  @Input() canCreate = false;
  @Input() addLabel = 'Add';

  @Output() rowClick = new EventEmitter<unknown>();
  @Output() actionClick = new EventEmitter<{ action: string; row: unknown }>();
  @Output() addClick = new EventEmitter<void>();
  @Output() pageChange = new EventEmitter<PageEvent>();
  @Output() sortChange = new EventEmitter<Sort>();
  @Output() search = new EventEmitter<string>();

  displayedColumns: string[] = [];
  searchQuery = '';

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['columns'] || changes['actions']) {
      this.displayedColumns = [
        ...this.columns.map(c => c.key),
        ...(this.actions.length > 0 ? ['actions'] : [])
      ];
    }
  }

  getCellValue(row: unknown, key: string): unknown {
    if (typeof row !== 'object' || row === null) return '';
    return (row as Record<string, unknown>)[key];
  }

  onRowClick(row: unknown): void {
    this.rowClick.emit(row);
  }

  onAction(action: string, row: unknown): void {
    this.actionClick.emit({ action, row });
  }

  onAdd(): void {
    this.addClick.emit();
  }

  onPage(event: PageEvent): void {
    this.pageChange.emit(event);
  }

  onSort(sort: Sort): void {
    this.sortChange.emit(sort);
  }

  onSearch(): void {
    this.search.emit(this.searchQuery);
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.search.emit('');
  }
}

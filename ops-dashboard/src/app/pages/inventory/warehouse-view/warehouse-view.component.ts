import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../../core/services/operations.service';
import {
  VirtualWarehouseLocation,
  VirtualWarehouseResponse,
  VirtualWarehouseTaskLink,
  VirtualWarehouseWorker,
  VirtualWarehouseZone
} from '../../../core/models/operations.model';
import { VirtualWarehouseSceneComponent } from './virtual-warehouse-scene.component';

@Component({
  selector: 'app-warehouse-view',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    PageHeaderComponent,
    VirtualWarehouseSceneComponent
  ],
  template: `
    <div class="warehouse-view-page">
      <app-page-header
        title="Warehouse View"
        description="A live virtual warehouse for stock, task flow, and worker movement."
        icon="warehouse">
        <button mat-stroked-button type="button" (click)="reload()">
          <mat-icon>refresh</mat-icon>
          Refresh
        </button>
      </app-page-header>

      <div class="controls-card" *ngIf="data() as vm">
        <mat-form-field appearance="outline" class="control-field search-field">
          <mat-label>Search location, SKU, or worker</mat-label>
          <mat-icon matPrefix>search</mat-icon>
          <input matInput [(ngModel)]="searchTerm" placeholder="LOC-001, SKU-001, Worker One">
        </mat-form-field>

        <mat-form-field appearance="outline" class="control-field zone-field">
          <mat-label>Zone</mat-label>
          <mat-select [(ngModel)]="zoneFilter">
            <mat-option value="">All Zones</mat-option>
            <mat-option *ngFor="let zone of vm.zones" [value]="zone.code">{{ zone.label }}</mat-option>
          </mat-select>
        </mat-form-field>

        <div class="toggle-group">
          <mat-slide-toggle [(ngModel)]="showWorkers">Show workers</mat-slide-toggle>
          <mat-slide-toggle [(ngModel)]="showTaskLinks">Show task links</mat-slide-toggle>
        </div>
      </div>

      <div class="loading-state" *ngIf="loading()">
        <mat-spinner diameter="44"></mat-spinner>
      </div>

      <ng-container *ngIf="!loading() && data() as vm">
        <div class="summary-strip">
          <div class="summary-pill">
            <span class="summary-label">In locations</span>
            <span class="summary-value">{{ asNumber(vm.summary.location_quantity) | number:'1.0-2' }}</span>
          </div>
          <div class="summary-pill summary-pill-warm">
            <span class="summary-label">With users</span>
            <span class="summary-value">{{ asNumber(vm.summary.user_quantity) | number:'1.0-2' }}</span>
          </div>
          <div class="summary-pill">
            <span class="summary-label">Active workers</span>
            <span class="summary-value">{{ vm.summary.workers_active }}</span>
          </div>
          <div class="summary-pill">
            <span class="summary-label">Unplaced</span>
            <span class="summary-value">{{ vm.summary.unplaced_location_count }}</span>
          </div>
        </div>

        <div class="layout-required" *ngIf="vm.locations.length === 0">
          <div class="layout-copy">
            <h3>Layout setup required</h3>
            <p>
              This facility has real locations mapped, but no <code>virtual_warehouse</code> coordinates in
              facility location overrides yet. Add layout metadata through the existing facility mapping paths,
              then reload this page.
            </p>
          </div>

          <div class="unplaced-panel" *ngIf="vm.unplaced_locations.length > 0">
            <div class="panel-title">Unplaced locations</div>
            <div class="unplaced-list">
              <div class="unplaced-row" *ngFor="let item of vm.unplaced_locations">
                <span class="unplaced-code">{{ item.code }}</span>
                <span class="unplaced-zone">{{ item.zone_code }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="warehouse-layout" *ngIf="vm.locations.length > 0">
          <section class="scene-card">
            <div class="scene-heading">
              <div>
                <h3>{{ vm.facility.name }}</h3>
                <p>{{ vm.facility.code }} · {{ vm.facility.warehouse_key }}</p>
              </div>
              <div class="scene-legend">
                <span class="legend-item"><span class="legend-dot legend-dot-stock"></span> Stocked rack</span>
                <span class="legend-item"><span class="legend-dot legend-dot-carry"></span> Carrying</span>
                <span class="legend-item"><span class="legend-dot legend-dot-drop"></span> Dropping</span>
              </div>
            </div>

            <app-virtual-warehouse-scene
              [scene]="vm.scene"
              [zones]="filteredZones(vm)"
              [locations]="filteredLocations(vm)"
              [workers]="visibleWorkers(vm)"
              [taskLinks]="visibleTaskLinks(vm)"
              [selectedLocationCode]="selectedLocationCode()"
              [selectedWorkerId]="selectedWorkerId()"
              [showWorkers]="showWorkers"
              [showTaskLinks]="showTaskLinks"
              (locationSelected)="selectLocation($event)"
              (workerSelected)="selectWorker($event)"
              (clearSelection)="clearSelection()">
            </app-virtual-warehouse-scene>

            <div class="scene-footer">
              <span>{{ filteredLocations(vm).length }} mapped locations visible</span>
              <span>{{ visibleWorkers(vm).length }} worker markers visible</span>
              <span *ngIf="vm.unplaced_locations.length > 0">{{ vm.unplaced_locations.length }} locations still unplaced</span>
            </div>
          </section>

          <aside class="detail-card">
            <ng-container *ngIf="selectedLocation(vm) as location; else workerSelection">
              <div class="detail-header">
                <div class="detail-kicker">Location</div>
                <h3>{{ location.code }}</h3>
                <p>{{ location.name }} · {{ location.zone_code }}</p>
              </div>

              <div class="detail-stats">
                <div class="detail-stat">
                  <span>On hand</span>
                  <strong>{{ asNumber(location.quantity_on_hand) | number:'1.0-2' }}</strong>
                </div>
                <div class="detail-stat">
                  <span>Available</span>
                  <strong>{{ asNumber(location.quantity_available) | number:'1.0-2' }}</strong>
                </div>
                <div class="detail-stat">
                  <span>Active tasks</span>
                  <strong>{{ location.active_tasks.length }}</strong>
                </div>
              </div>

              <div class="detail-section">
                <div class="section-title">Stock at this location</div>
                <div class="empty-copy" *ngIf="location.stock_items.length === 0">No stock recorded here.</div>
                <div class="stock-list" *ngIf="location.stock_items.length > 0">
                  <div class="stock-row" *ngFor="let item of location.stock_items">
                    <div>
                      <div class="stock-code">{{ item.sku_code }}</div>
                      <div class="stock-name">{{ item.sku_name }}</div>
                    </div>
                    <div class="stock-qty">{{ asNumber(item.quantity_on_hand) | number:'1.0-2' }}</div>
                  </div>
                </div>
              </div>

              <div class="detail-section">
                <div class="section-title">Active tasks</div>
                <div class="empty-copy" *ngIf="location.active_tasks.length === 0">No live task activity here.</div>
                <div class="task-list" *ngIf="location.active_tasks.length > 0">
                  <div class="task-row" *ngFor="let task of location.active_tasks">
                    <div class="task-main">
                      <span class="task-type">{{ task.task_type }}</span>
                      <span class="task-sku">{{ task.sku_code }}</span>
                    </div>
                    <div class="task-sub">
                      {{ asNumber(task.quantity) | number:'1.0-2' }}
                      <span *ngIf="task.counterpart_entity_code">· {{ task.counterpart_entity_code }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="detail-section">
                <div class="section-title">Linked workers</div>
                <div class="empty-copy" *ngIf="relatedWorkers(vm, location).length === 0">No worker markers linked.</div>
                <button
                  type="button"
                  class="worker-chip"
                  *ngFor="let worker of relatedWorkers(vm, location)"
                  (click)="selectWorker(worker)">
                  <span class="worker-chip-state" [class]="'state-' + worker.state"></span>
                  {{ worker.display_name }}
                </button>
              </div>
            </ng-container>

            <ng-template #workerSelection>
              <ng-container *ngIf="selectedWorker(vm) as worker; else defaultPanel">
                <div class="detail-header">
                  <div class="detail-kicker">Worker</div>
                  <h3>{{ worker.display_name }}</h3>
                  <p>{{ worker.state | titlecase }} · {{ worker.task_type | uppercase }}</p>
                </div>

                <div class="detail-stats">
                  <div class="detail-stat">
                    <span>SKU</span>
                    <strong>{{ worker.sku_code }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Qty</span>
                    <strong>{{ asNumber(worker.quantity) | number:'1.0-2' }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Age</span>
                    <strong>{{ taskAge(worker) }}</strong>
                  </div>
                </div>

                <div class="detail-section">
                  <div class="section-title">Route</div>
                  <div class="route-card">
                    <div><span>From</span><strong>{{ worker.source_entity_code || '—' }}</strong></div>
                    <div><span>To</span><strong>{{ worker.dest_entity_code || '—' }}</strong></div>
                  </div>
                </div>

                <div class="detail-section">
                  <div class="section-title">Task details</div>
                  <div class="task-list">
                    <div class="task-row">
                      <div class="task-main">
                        <span class="task-type">{{ worker.task_status }}</span>
                        <span class="task-sku">{{ worker.sku_name }}</span>
                      </div>
                      <div class="task-sub">{{ worker.task_type }} · {{ worker.task_id }}</div>
                    </div>
                  </div>
                </div>

                <div class="detail-section" *ngIf="workerLink(vm, worker) as link">
                  <div class="section-title">Movement link</div>
                  <div class="route-card">
                    <div><span>Source</span><strong>{{ link.source_entity_code }}</strong></div>
                    <div><span>Destination</span><strong>{{ link.dest_entity_code }}</strong></div>
                  </div>
                </div>
              </ng-container>
            </ng-template>

            <ng-template #defaultPanel>
              <div class="detail-header">
                <div class="detail-kicker">Selection</div>
                <h3>Warehouse details</h3>
                <p>Select a location or worker pin to inspect live stock and task flow.</p>
              </div>

              <div class="detail-section">
              <div class="section-title">What this view shows</div>
              <div class="info-list">
                  <div class="info-row">Locations are rendered from <code>virtual_warehouse</code> overrides.</div>
                  <div class="info-row">Color intensity reflects stock currently on hand.</div>
                  <div class="info-row">Worker pins come from active pick/drop task state.</div>
                  <div class="info-row">Curved links show stock that was picked but not yet dropped.</div>
                </div>
              </div>

              <div class="detail-section" *ngIf="vm.unplaced_locations.length > 0">
                <div class="section-title">Still unplaced</div>
                <div class="unplaced-list">
                  <div class="unplaced-row" *ngFor="let item of vm.unplaced_locations">
                    <span class="unplaced-code">{{ item.code }}</span>
                    <span class="unplaced-zone">{{ item.zone_code }}</span>
                  </div>
                </div>
              </div>
            </ng-template>
          </aside>
        </div>
      </ng-container>
    </div>
  `,
  styles: [':host { display: block; }']
})
export class WarehouseViewComponent implements OnInit {
  private readonly operations = inject(OperationsService);
  private readonly snackBar = inject(MatSnackBar);

  readonly data = signal<VirtualWarehouseResponse | null>(null);
  readonly loading = signal(true);
  readonly selectedLocationCode = signal<string | null>(null);
  readonly selectedWorkerId = signal<string | null>(null);

  searchTerm = '';
  zoneFilter = '';
  showWorkers = true;
  showTaskLinks = true;

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.loading.set(true);
    this.operations.getVirtualWarehouse().subscribe({
      next: (response) => {
        this.data.set(response);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('Failed to load warehouse view', 'Dismiss', { duration: 4000 });
        this.loading.set(false);
      }
    });
  }

  filteredZones(vm: VirtualWarehouseResponse): VirtualWarehouseZone[] {
    if (!this.zoneFilter) {
      return vm.zones;
    }
    return vm.zones.filter((zone) => zone.code === this.zoneFilter);
  }

  filteredLocations(vm: VirtualWarehouseResponse): VirtualWarehouseLocation[] {
    const search = this.normalizedSearch();
    return vm.locations.filter((location) => {
      if (this.zoneFilter && location.zone_code !== this.zoneFilter) {
        return false;
      }
      if (!search) {
        return true;
      }
      const haystack = [
        location.code,
        location.name,
        location.zone_code,
        ...location.stock_items.map((item) => `${item.sku_code} ${item.sku_name}`),
        ...location.active_tasks.map((task) => `${task.sku_code} ${task.sku_name} ${task.assigned_to_name ?? ''}`),
      ].join(' ').toLowerCase();
      return haystack.includes(search);
    });
  }

  visibleWorkers(vm: VirtualWarehouseResponse): VirtualWarehouseWorker[] {
    if (!this.showWorkers) {
      return [];
    }
    return this.matchingWorkers(vm);
  }

  visibleTaskLinks(vm: VirtualWarehouseResponse): VirtualWarehouseTaskLink[] {
    if (!this.showTaskLinks) {
      return [];
    }
    const visibleWorkerIds = new Set(this.matchingWorkers(vm).map((worker) => worker.id));
    return vm.task_links.filter((link) => visibleWorkerIds.has(link.worker_id));
  }

  matchingWorkers(vm: VirtualWarehouseResponse): VirtualWarehouseWorker[] {
    const visibleLocations = this.filteredLocations(vm);
    const visibleLocationCodes = new Set(visibleLocations.map((location) => location.code));
    const search = this.normalizedSearch();

    return vm.workers.filter((worker) => {
      const matchesZone = !this.zoneFilter
        || worker.source_entity_code != null && visibleLocationCodes.has(worker.source_entity_code)
        || worker.dest_entity_code != null && visibleLocationCodes.has(worker.dest_entity_code);

      if (!matchesZone) {
        return false;
      }

      if (!search) {
        return true;
      }

      const haystack = [
        worker.display_name,
        worker.sku_code,
        worker.sku_name,
        worker.source_entity_code ?? '',
        worker.dest_entity_code ?? '',
      ].join(' ').toLowerCase();
      return haystack.includes(search);
    });
  }

  selectedLocation(vm: VirtualWarehouseResponse): VirtualWarehouseLocation | null {
    return vm.locations.find((location) => location.code === this.selectedLocationCode()) ?? null;
  }

  selectedWorker(vm: VirtualWarehouseResponse): VirtualWarehouseWorker | null {
    return vm.workers.find((worker) => worker.id === this.selectedWorkerId()) ?? null;
  }

  relatedWorkers(vm: VirtualWarehouseResponse, location: VirtualWarehouseLocation): VirtualWarehouseWorker[] {
    const relatedUserIds = new Set(location.worker_ids);
    return vm.workers.filter((worker) => relatedUserIds.has(worker.user_id));
  }

  workerLink(vm: VirtualWarehouseResponse, worker: VirtualWarehouseWorker): VirtualWarehouseTaskLink | null {
    return vm.task_links.find((link) => link.worker_id === worker.id) ?? null;
  }

  selectLocation(location: VirtualWarehouseLocation): void {
    this.selectedLocationCode.set(location.code);
    this.selectedWorkerId.set(null);
  }

  selectWorker(worker: VirtualWarehouseWorker): void {
    this.selectedWorkerId.set(worker.id);
    this.selectedLocationCode.set(null);
  }

  clearSelection(): void {
    this.selectedLocationCode.set(null);
    this.selectedWorkerId.set(null);
  }

  asNumber(value: string | number): number {
    return Number(value || 0);
  }

  taskAge(worker: VirtualWarehouseWorker): string {
    const anchor = worker.task_completed_at || worker.task_started_at || worker.assigned_at;
    if (!anchor) {
      return '—';
    }
    const deltaMinutes = Math.max(Math.round((Date.now() - new Date(anchor).getTime()) / 60000), 0);
    if (deltaMinutes < 60) {
      return `${deltaMinutes}m`;
    }
    const hours = Math.floor(deltaMinutes / 60);
    const minutes = deltaMinutes % 60;
    return `${hours}h ${minutes}m`;
  }

  private normalizedSearch(): string {
    return this.searchTerm.trim().toLowerCase();
  }
}

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import {
  VirtualWarehouseLocation,
  VirtualWarehouseScene,
  VirtualWarehouseTaskLink,
  VirtualWarehouseWorker,
  VirtualWarehouseZone
} from '../../../core/models/operations.model';

@Component({
  selector: 'app-virtual-warehouse-scene',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="scene-shell">
      <svg
        class="scene-canvas"
        [attr.viewBox]="'0 0 ' + scene.width + ' ' + scene.height"
        preserveAspectRatio="xMidYMid meet"
        (click)="clearSelection.emit()">

        <defs>
          <linearGradient id="warehouse-floor" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="rgba(255,255,255,0.98)"></stop>
            <stop offset="100%" stop-color="rgba(233, 239, 247, 0.9)"></stop>
          </linearGradient>
          <filter id="scene-shadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="20" stdDeviation="18" flood-color="rgba(15, 23, 42, 0.2)"></feDropShadow>
          </filter>
        </defs>

        <polygon
          class="warehouse-floor"
          [attr.points]="floorPoints()"
          fill="url(#warehouse-floor)"
          filter="url(#scene-shadow)">
        </polygon>

        <g class="warehouse-areas">
          <g *ngFor="let area of scene.areas">
            <rect
              class="area-card"
              [attr.x]="area.x"
              [attr.y]="area.y"
              [attr.width]="area.w"
              [attr.height]="area.h"
              rx="20"
              [attr.fill]="areaFill(area.kind)">
            </rect>
            <text
              class="area-label"
              [attr.x]="area.x + 18"
              [attr.y]="area.y + 30">
              {{ area.label }}
            </text>
          </g>
        </g>

        <g class="warehouse-zones">
          <g *ngFor="let zone of zones">
            <rect
              class="zone-floor"
              [attr.x]="zone.x"
              [attr.y]="zone.y"
              [attr.width]="zone.w"
              [attr.height]="zone.h"
              rx="24"
              [attr.fill]="zoneFill(zone.kind)">
              </rect>
            <text
              class="zone-label"
              [attr.x]="zone.x + 18"
              [attr.y]="zone.y + 28">
              {{ zone.label }}
            </text>
          </g>
        </g>

        <g class="warehouse-links" *ngIf="showTaskLinks">
          <path
            *ngFor="let link of taskLinks"
            class="task-link"
            [class.task-link-selected]="link.worker_id === selectedWorkerId"
            [attr.d]="taskPath(link)"
            [attr.stroke]="taskLinkColor(link.state)">
          </path>
        </g>

        <g class="warehouse-locations">
          <g
            *ngFor="let location of locations"
            class="location-node"
            [class.location-selected]="location.code === selectedLocationCode"
            [attr.transform]="locationTransform(location)"
            (click)="handleLocationClick(location, $event)">
            <polygon
              class="location-top"
              [attr.points]="topFacePoints(location)"
              [attr.fill]="locationTopFill(location)">
            </polygon>
            <polygon
              class="location-left"
              [attr.points]="leftFacePoints(location)"
              [attr.fill]="locationSideFill(location, 'left')">
            </polygon>
            <polygon
              class="location-right"
              [attr.points]="rightFacePoints(location)"
              [attr.fill]="locationSideFill(location, 'right')">
            </polygon>
            <rect
              *ngIf="location.active_tasks.length > 0"
              class="location-glow"
              x="-6"
              y="-6"
              [attr.width]="location.w + 12"
              [attr.height]="location.h + locationDepth(location) + 14"
              rx="14">
            </rect>
            <text
              class="location-label"
              [attr.x]="location.w / 2"
              [attr.y]="location.h + locationDepth(location) + 22">
              {{ location.code }}
            </text>
          </g>
        </g>

        <g class="warehouse-workers" *ngIf="showWorkers">
          <g
            *ngFor="let worker of workers"
            class="worker-node"
            [class.worker-selected]="worker.id === selectedWorkerId"
            [attr.transform]="'translate(' + worker.x + ',' + worker.y + ')'"
            (click)="handleWorkerClick(worker, $event)">
            <circle class="worker-shadow" r="16" cx="0" cy="0"></circle>
            <circle
              class="worker-body"
              r="12"
              cx="0"
              cy="0"
              [attr.fill]="workerColor(worker.state)">
            </circle>
            <circle class="worker-core" r="4" cx="0" cy="0"></circle>
            <text class="worker-label" x="18" y="4">{{ worker.display_name }}</text>
          </g>
        </g>
      </svg>
    </div>
  `,
  styles: [`
    .scene-shell {
      position: relative;
      width: 100%;
      border-radius: 28px;
      overflow: hidden;
      border: 1px solid rgba(148, 163, 184, 0.24);
      background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.94), transparent 28%),
        linear-gradient(160deg, rgba(97, 166, 219, 0.18), rgba(241, 245, 249, 0.08) 48%, rgba(248, 250, 252, 0.92));
      min-height: 520px;
    }
    .scene-canvas {
      width: 100%;
      height: auto;
      display: block;
      cursor: grab;
    }
    .warehouse-floor {
      stroke: rgba(148, 163, 184, 0.2);
      stroke-width: 2;
    }
    .area-card {
      stroke: rgba(71, 85, 105, 0.18);
      stroke-width: 2;
      stroke-dasharray: 8 8;
    }
    .area-label,
    .zone-label {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.04em;
      fill: rgba(15, 23, 42, 0.72);
    }
    .zone-floor {
      stroke: rgba(71, 85, 105, 0.16);
      stroke-width: 2;
    }
    .task-link {
      fill: none;
      stroke-width: 4;
      stroke-linecap: round;
      stroke-dasharray: 12 12;
      opacity: 0.7;
    }
    .task-link-selected {
      stroke-width: 6;
      opacity: 1;
    }
    .location-node {
      cursor: pointer;
    }
    .location-top,
    .location-left,
    .location-right {
      stroke: rgba(15, 23, 42, 0.14);
      stroke-width: 1.5;
      transition: transform 0.18s ease, opacity 0.18s ease;
    }
    .location-glow {
      fill: rgba(245, 158, 11, 0.12);
      stroke: rgba(245, 158, 11, 0.4);
      stroke-width: 2;
    }
    .location-selected .location-top,
    .location-selected .location-left,
    .location-selected .location-right {
      stroke: rgba(245, 158, 11, 0.9);
      stroke-width: 2.5;
    }
    .location-label {
      font-size: 13px;
      font-weight: 700;
      text-anchor: middle;
      fill: rgba(15, 23, 42, 0.8);
      pointer-events: none;
    }
    .worker-node {
      cursor: pointer;
    }
    .worker-shadow {
      fill: rgba(15, 23, 42, 0.16);
    }
    .worker-body {
      stroke: rgba(255, 255, 255, 0.92);
      stroke-width: 3;
    }
    .worker-core {
      fill: rgba(255, 255, 255, 0.88);
    }
    .worker-selected .worker-body {
      stroke: rgba(15, 23, 42, 0.92);
      stroke-width: 4;
    }
    .worker-label {
      font-size: 14px;
      font-weight: 700;
      fill: rgba(15, 23, 42, 0.84);
      paint-order: stroke;
      stroke: rgba(255, 255, 255, 0.95);
      stroke-width: 4;
      stroke-linejoin: round;
    }
  `]
})
export class VirtualWarehouseSceneComponent implements OnChanges {
  @Input({ required: true }) scene: VirtualWarehouseScene = { width: 1600, height: 900, areas: [] };
  @Input() zones: VirtualWarehouseZone[] = [];
  @Input() locations: VirtualWarehouseLocation[] = [];
  @Input() workers: VirtualWarehouseWorker[] = [];
  @Input() taskLinks: VirtualWarehouseTaskLink[] = [];
  @Input() selectedLocationCode: string | null = null;
  @Input() selectedWorkerId: string | null = null;
  @Input() showWorkers = true;
  @Input() showTaskLinks = true;

  @Output() locationSelected = new EventEmitter<VirtualWarehouseLocation>();
  @Output() workerSelected = new EventEmitter<VirtualWarehouseWorker>();
  @Output() clearSelection = new EventEmitter<void>();

  private maxLocationQuantity = 1;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['locations']) {
      const quantities = this.locations.map((location) => Number(location.quantity_on_hand || 0));
      this.maxLocationQuantity = Math.max(...quantities, 1);
    }
  }

  floorPoints(): string {
    const width = this.scene.width;
    const height = this.scene.height;
    return `120,${height - 180} ${width / 2},140 ${width - 120},${height - 220} ${width / 2},${height - 40}`;
  }

  areaFill(kind: string): string {
    const fills: Record<string, string> = {
      dispatch: 'rgba(251, 191, 36, 0.16)',
      receiving: 'rgba(59, 130, 246, 0.12)',
      service: 'rgba(148, 163, 184, 0.16)'
    };
    return fills[kind] ?? 'rgba(148, 163, 184, 0.12)';
  }

  zoneFill(kind: string): string {
    const fills: Record<string, string> = {
      storage: 'rgba(255, 255, 255, 0.58)',
      staging: 'rgba(99, 102, 241, 0.12)',
      dispatch: 'rgba(251, 191, 36, 0.12)',
      receiving: 'rgba(59, 130, 246, 0.1)',
      service: 'rgba(148, 163, 184, 0.12)'
    };
    return fills[kind] ?? 'rgba(255, 255, 255, 0.42)';
  }

  locationDepth(location: VirtualWarehouseLocation): number {
    return Math.max(Math.round(location.h * 0.7), 14);
  }

  locationTransform(location: VirtualWarehouseLocation): string {
    const originX = location.w / 2;
    const originY = location.h / 2;
    return `translate(${location.x},${location.y}) rotate(${location.rotation} ${originX} ${originY})`;
  }

  topFacePoints(location: VirtualWarehouseLocation): string {
    const depth = this.locationDepth(location);
    const halfWidth = location.w / 2;
    return `0,${depth / 2} ${halfWidth},0 ${location.w},${depth / 2} ${halfWidth},${depth}`;
  }

  leftFacePoints(location: VirtualWarehouseLocation): string {
    const depth = this.locationDepth(location);
    const halfWidth = location.w / 2;
    return `0,${depth / 2} ${halfWidth},${depth} ${halfWidth},${depth + location.h} 0,${depth / 2 + location.h}`;
  }

  rightFacePoints(location: VirtualWarehouseLocation): string {
    const depth = this.locationDepth(location);
    const halfWidth = location.w / 2;
    return `${location.w},${depth / 2} ${halfWidth},${depth} ${halfWidth},${depth + location.h} ${location.w},${depth / 2 + location.h}`;
  }

  locationTopFill(location: VirtualWarehouseLocation): string {
    const intensity = Number(location.quantity_on_hand || 0) / this.maxLocationQuantity;
    const base = this.locationBaseColor(location.kind);
    const alpha = Math.min(0.38 + intensity * 0.46, 0.92);
    return `rgba(${base.join(',')}, ${alpha.toFixed(2)})`;
  }

  locationSideFill(location: VirtualWarehouseLocation, side: 'left' | 'right'): string {
    const intensity = Number(location.quantity_on_hand || 0) / this.maxLocationQuantity;
    const base = this.locationBaseColor(location.kind);
    const adjustment = side === 'left' ? 0.16 : 0.08;
    const alpha = Math.min(0.48 + intensity * 0.38 + adjustment, 0.98);
    return `rgba(${base.join(',')}, ${alpha.toFixed(2)})`;
  }

  locationBaseColor(kind: string): [number, number, number] {
    const palette: Record<string, [number, number, number]> = {
      rack: [245, 158, 11],
      floor: [59, 130, 246],
      dock: [71, 85, 105]
    };
    return palette[kind] ?? [234, 179, 8];
  }

  taskPath(link: VirtualWarehouseTaskLink): string {
    const midX = (link.source_x + link.dest_x) / 2;
    const curveLift = Math.max(42, Math.abs(link.dest_x - link.source_x) * 0.08);
    const midY = ((link.source_y + link.dest_y) / 2) - curveLift;
    return `M ${link.source_x} ${link.source_y} Q ${midX} ${midY} ${link.dest_x} ${link.dest_y}`;
  }

  taskLinkColor(state: string): string {
    return state === 'dropping' ? 'rgba(239, 68, 68, 0.72)' : 'rgba(249, 115, 22, 0.76)';
  }

  workerColor(state: string): string {
    const colors: Record<string, string> = {
      picking: '#2563eb',
      carrying: '#f59e0b',
      dropping: '#ef4444'
    };
    return colors[state] ?? '#475569';
  }

  handleLocationClick(location: VirtualWarehouseLocation, event: Event): void {
    event.stopPropagation();
    this.locationSelected.emit(location);
  }

  handleWorkerClick(worker: VirtualWarehouseWorker, event: Event): void {
    event.stopPropagation();
    this.workerSelected.emit(worker);
  }
}

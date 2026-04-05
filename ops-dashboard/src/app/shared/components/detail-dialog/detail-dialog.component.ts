import {
  Component, Input, Output, EventEmitter, TemplateRef,
  ContentChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { trigger, state, style, animate, transition } from '@angular/animations';

@Component({
  selector: 'app-detail-dialog',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatDividerModule],
  animations: [
    trigger('slideIn', [
      state('void', style({ opacity: 0 })),
      state('*', style({ opacity: 1 })),
      transition('void => *', animate('200ms ease')),
      transition('* => void', animate('150ms ease'))
    ])
  ],
  template: `
    <div class="dialog-backdrop" *ngIf="open" [@slideIn] (click)="onBackdropClick($event)">
      <div class="dialog-panel" (click)="$event.stopPropagation()">
        <!-- Header -->
        <div class="dialog-header">
          <div class="dialog-title-area">
            <button mat-icon-button type="button" class="back-btn" (click)="onClose($event)">
              <mat-icon>arrow_back</mat-icon>
            </button>
            <div>
              <h2 class="dialog-title">{{ title }}</h2>
              <p class="dialog-subtitle" *ngIf="subtitle">{{ subtitle }}</p>
            </div>
          </div>
          <div class="dialog-header-actions">
            <ng-content select="[header-actions]"></ng-content>
          </div>
        </div>
        <mat-divider></mat-divider>

        <!-- Content -->
        <div class="dialog-content">
          <ng-content></ng-content>
        </div>

        <!-- Footer -->
        <div class="dialog-footer" *ngIf="showFooter">
          <mat-divider></mat-divider>
          <div class="footer-actions">
            <button mat-stroked-button type="button" (click)="onClose($event)">Cancel</button>
            <ng-content select="[footer-actions]"></ng-content>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dialog-backdrop {
      position: fixed;
      inset: 0;
      background: var(--ops-overlay);
      backdrop-filter: blur(8px);
      z-index: 1000;
      display: flex;
      align-items: flex-end;
    }
    .dialog-panel {
      background: var(--ops-elevated-bg);
      border: 1px solid var(--ops-border);
      width: 100%;
      max-height: 92vh;
      border-radius: 20px 20px 0 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: var(--ops-shadow);
      transform: translateY(0);
      transition: transform 200ms cubic-bezier(0.4, 0, 0.2, 1);
    }
    .dialog-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 8px 12px 4px;
      flex-shrink: 0;
      background: var(--ops-glass-soft);
    }
    .dialog-title-area {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .back-btn {
      color: var(--ops-text-muted);
      background: var(--ops-item-hover);
    }
    .dialog-title {
      font-size: 18px;
      font-weight: 600;
      color: var(--ops-text);
      margin: 0;
    }
    .dialog-subtitle {
      font-size: 13px;
      color: var(--ops-text-muted);
      margin: 2px 0 0;
    }
    .dialog-header-actions {
      display: flex;
      gap: 8px;
    }
    .dialog-content {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      color: var(--ops-text);
    }
    .dialog-footer {
      flex-shrink: 0;
      background: var(--ops-item-hover);
    }
    .footer-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 12px 16px;
    }

    @media (min-width: 768px) {
      .dialog-backdrop {
        align-items: center;
        justify-content: center;
      }
      .dialog-panel {
        width: 640px;
        max-width: 90vw;
        max-height: 85vh;
        border-radius: 20px;
      }
    }
  `]
})
export class DetailDialogComponent {
  @Input() open = false;
  @Input() title = '';
  @Input() subtitle = '';
  @Input() showFooter = false;
  @Output() closed = new EventEmitter<void>();

  onClose(event?: Event): void {
    event?.preventDefault();
    event?.stopPropagation();
    this.closed.emit();
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      this.onClose();
    }
  }
}

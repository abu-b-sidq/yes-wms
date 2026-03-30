import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="page-header">
      <div class="header-main">
        <div class="header-icon" *ngIf="icon">
          <mat-icon>{{ icon }}</mat-icon>
        </div>
        <div class="header-text">
          <h1 class="header-title">{{ title }}</h1>
          <p class="header-desc" *ngIf="description">{{ description }}</p>
        </div>
      </div>
      <div class="header-actions">
        <ng-content></ng-content>
      </div>
    </div>
  `,
  styles: [`
    .page-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 24px 24px 16px;
      gap: 16px;
      flex-wrap: wrap;
    }
    .header-main {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .header-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      background: #eff6ff;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .header-icon mat-icon {
      color: #3b82f6;
      font-size: 22px;
      width: 22px;
      height: 22px;
    }
    .header-title {
      font-size: 22px;
      font-weight: 700;
      color: #1e293b;
      margin: 0;
    }
    .header-desc {
      font-size: 13px;
      color: #64748b;
      margin: 2px 0 0;
    }
    .header-actions {
      display: flex;
      gap: 8px;
    }
  `]
})
export class PageHeaderComponent {
  @Input() title = '';
  @Input() description = '';
  @Input() icon = '';
}

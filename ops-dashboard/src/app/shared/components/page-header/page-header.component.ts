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
      padding: 30px 24px 20px;
      gap: 16px;
      flex-wrap: wrap;
    }
    .header-main {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .header-icon {
      width: 46px;
      height: 46px;
      border-radius: 14px;
      background: linear-gradient(180deg, var(--ops-primary-soft-strong) 0%, transparent 100%);
      border: 1px solid var(--ops-border);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--ops-shadow-soft);
    }
    .header-icon mat-icon {
      color: var(--ops-primary);
      font-size: 22px;
      width: 22px;
      height: 22px;
    }
    .header-title {
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.04em;
      color: var(--ops-text);
      margin: 0;
    }
    .header-desc {
      font-size: 14px;
      color: var(--ops-text-muted);
      margin: 4px 0 0;
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

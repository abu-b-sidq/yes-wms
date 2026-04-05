import { Component, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { filter } from 'rxjs/operators';
import { SidebarComponent } from '../sidebar/sidebar.component';

type PageScene =
  | 'dashboard'
  | 'sku'
  | 'zone'
  | 'location'
  | 'transactions'
  | 'grn'
  | 'move'
  | 'putaway'
  | 'order-pick'
  | 'inventory'
  | 'connectors'
  | 'connector-logs';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, MatIconModule],
  template: `
    <div class="shell" [class.mobile-overlay-open]="!sidebarCollapsed && isMobile()">
      <!-- Mobile overlay -->
      <div class="mobile-overlay"
           *ngIf="!sidebarCollapsed && isMobile()"
           (click)="sidebarCollapsed = true">
      </div>

      <button
        type="button"
        class="mobile-nav-trigger"
        *ngIf="isMobile() && sidebarCollapsed"
        (click)="toggleSidebar()"
        aria-label="Open navigation">
        <mat-icon>menu</mat-icon>
      </button>

      <!-- Sidebar -->
      <div class="sidebar-wrapper" [class.mobile-sidebar]="isMobile()"
           [class.mobile-hidden]="isMobile() && sidebarCollapsed">
        <app-sidebar
          [collapsed]="!isMobile() && sidebarCollapsed"
          (toggleCollapse)="sidebarCollapsed = !sidebarCollapsed">
        </app-sidebar>
      </div>

      <!-- Main content -->
      <div
        class="main-content"
        [class.sidebar-collapsed]="sidebarCollapsed"
        [attr.data-scene]="pageScene()">
        <main class="page-content">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .shell {
      display: flex;
      height: 100vh;
      overflow: hidden;
      background: var(--ops-shell-bg);
    }
    .sidebar-wrapper {
      flex-shrink: 0;
      height: 100%;
      z-index: 100;
    }
    .main-content {
      flex: 1;
      position: relative;
      isolation: isolate;
      display: flex;
      flex-direction: column;
      min-width: 0;
      background: var(--ops-page-layer, var(--ops-page-bg));
      transition: margin-left 0.3s ease;
    }
    .main-content::before,
    .main-content::after {
      content: '';
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .main-content::before {
      z-index: 0;
      background:
        radial-gradient(circle at 82% 12%, var(--ops-scene-glow, rgba(121, 191, 100, 0.12)), transparent 24%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 34%);
    }
    .main-content::after {
      z-index: 0;
      background-image: var(--ops-scene-art, none);
      background-repeat: no-repeat;
      background-position: right clamp(-88px, -6vw, -24px) top 20px;
      background-size: min(760px, 58vw) auto;
      opacity: var(--ops-scene-opacity, 0.24);
      filter: saturate(1.02);
    }
    .page-content {
      flex: 1;
      position: relative;
      z-index: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 0;
      background: transparent;
    }
    .mobile-nav-trigger {
      position: fixed;
      top: 18px;
      left: 18px;
      width: 48px;
      height: 48px;
      border: 1px solid var(--ops-border);
      border-radius: 16px;
      background: var(--ops-glass);
      color: var(--ops-text);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--ops-shadow-soft);
      backdrop-filter: blur(18px);
      z-index: 101;
      cursor: pointer;
    }
    .mobile-sidebar {
      position: fixed;
      left: 0;
      top: 0;
      height: 100%;
      box-shadow: var(--ops-shadow);
    }
    .mobile-hidden {
      transform: translateX(-100%);
      transition: transform 0.3s ease;
    }
    .mobile-overlay {
      position: fixed;
      inset: 0;
      background: var(--ops-overlay);
      backdrop-filter: blur(6px);
      z-index: 99;
    }

    @media (max-width: 768px) {
      .main-content {
        margin-left: 0 !important;
      }

      .page-content {
        padding-top: 72px;
      }

      .main-content::after {
        background-position: right -160px top 36px;
        background-size: 620px auto;
      }
    }
  `]
})
export class ShellComponent {
  sidebarCollapsed = false;
  readonly pageScene = signal<PageScene>('dashboard');
  private readonly router = inject(Router);
  private _isMobile = signal(window.innerWidth <= 768);

  isMobile = this._isMobile;

  constructor() {
    this.syncScene(this.router.url);
    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event) => this.syncScene(event.urlAfterRedirects));

    this._isMobile.set(window.innerWidth <= 768);
    if (this._isMobile()) {
      this.sidebarCollapsed = true;
    }
  }

  @HostListener('window:resize')
  onResize(): void {
    const mobile = window.innerWidth <= 768;
    this._isMobile.set(mobile);
    if (mobile && !this.sidebarCollapsed) {
      this.sidebarCollapsed = true;
    }
  }

  toggleSidebar(): void {
    this.sidebarCollapsed = !this.sidebarCollapsed;
  }

  private syncScene(url: string): void {
    if (url.startsWith('/transactions/grn')) {
      this.pageScene.set('grn');
      return;
    }
    if (url.startsWith('/transactions/move')) {
      this.pageScene.set('move');
      return;
    }
    if (url.startsWith('/transactions/putaway')) {
      this.pageScene.set('putaway');
      return;
    }
    if (url.startsWith('/transactions/order-pick')) {
      this.pageScene.set('order-pick');
      return;
    }
    if (url.startsWith('/transactions')) {
      this.pageScene.set('transactions');
      return;
    }
    if (url.startsWith('/masters/sku')) {
      this.pageScene.set('sku');
      return;
    }
    if (url.startsWith('/masters/zone')) {
      this.pageScene.set('zone');
      return;
    }
    if (url.startsWith('/masters/location')) {
      this.pageScene.set('location');
      return;
    }
    if (url.startsWith('/inventory')) {
      this.pageScene.set('inventory');
      return;
    }
    if (url.startsWith('/connectors/') && url.includes('/logs')) {
      this.pageScene.set('connector-logs');
      return;
    }
    if (url.startsWith('/connectors')) {
      this.pageScene.set('connectors');
      return;
    }

    this.pageScene.set('dashboard');
  }
}

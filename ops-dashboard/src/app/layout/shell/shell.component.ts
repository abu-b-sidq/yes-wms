import { Component, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { filter, map } from 'rxjs/operators';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { TopbarComponent } from '../topbar/topbar.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, TopbarComponent],
  template: `
    <div class="shell" [class.mobile-overlay-open]="!sidebarCollapsed && isMobile()">
      <!-- Mobile overlay -->
      <div class="mobile-overlay"
           *ngIf="!sidebarCollapsed && isMobile()"
           (click)="sidebarCollapsed = true">
      </div>

      <!-- Sidebar -->
      <div class="sidebar-wrapper" [class.mobile-sidebar]="isMobile()"
           [class.mobile-hidden]="isMobile() && sidebarCollapsed">
        <app-sidebar
          [collapsed]="!isMobile() && sidebarCollapsed"
          (toggleCollapse)="sidebarCollapsed = !sidebarCollapsed">
        </app-sidebar>
      </div>

      <!-- Main content -->
      <div class="main-content" [class.sidebar-collapsed]="sidebarCollapsed">
        <app-topbar
          [sidebarCollapsed]="sidebarCollapsed"
          [title]="pageTitle()"
          (toggleSidebar)="toggleSidebar()">
        </app-topbar>

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
      background:
        radial-gradient(circle at top right, rgba(75, 152, 235, 0.16), transparent 26%),
        linear-gradient(180deg, #14191e 0%, #191e23 100%);
    }
    .sidebar-wrapper {
      flex-shrink: 0;
      height: 100%;
      z-index: 100;
    }
    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      background: transparent;
      transition: margin-left 0.3s ease;
    }
    .page-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 0;
      background: transparent;
    }
    .mobile-sidebar {
      position: fixed;
      left: 0;
      top: 0;
      height: 100%;
      box-shadow: 16px 0 40px rgba(0,0,0,0.35);
    }
    .mobile-hidden {
      transform: translateX(-100%);
      transition: transform 0.3s ease;
    }
    .mobile-overlay {
      position: fixed;
      inset: 0;
      background: rgba(20, 25, 30, 0.78);
      backdrop-filter: blur(6px);
      z-index: 99;
    }

    @media (max-width: 768px) {
      .main-content {
        margin-left: 0 !important;
      }
    }
  `]
})
export class ShellComponent {
  sidebarCollapsed = false;
  pageTitle = signal('Dashboard');
  private _isMobile = signal(window.innerWidth <= 768);

  isMobile = this._isMobile;

  constructor(private router: Router, private route: ActivatedRoute) {
    this._isMobile.set(window.innerWidth <= 768);
    if (this._isMobile()) {
      this.sidebarCollapsed = true;
    }

    this.router.events.pipe(
      filter(e => e instanceof NavigationEnd),
      map(() => {
        let r = this.route;
        while (r.firstChild) r = r.firstChild;
        return r.snapshot.data['title'] as string ?? 'Dashboard';
      })
    ).subscribe(title => this.pageTitle.set(title));
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
}

import { Component, Input, Output, EventEmitter, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavigationEnd, Router, RouterModule } from '@angular/router';
import { filter } from 'rxjs/operators';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from '../../core/auth/auth.service';

type WorkspaceMode = 'operate' | 'setup';

interface NavItem {
  label: string;
  icon: string;
  route?: string;
  badge?: string | number;
  exact?: boolean;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatTooltipModule
  ],
  template: `
    <aside class="sidebar-shell" [class.collapsed]="collapsed">
      <div class="sidebar-panel">
        <div class="sidebar-header">
          <div class="brand-row">
            <div class="brand-mark">
              <mat-icon>warehouse</mat-icon>
            </div>

            <div class="brand-copy" *ngIf="!collapsed">
              <div class="brand-title">YES WMS</div>
              <div class="brand-caption">Operations Console</div>
            </div>
          </div>

          <button
            type="button"
            class="icon-button"
            (click)="toggleCollapse.emit()"
            [matTooltip]="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
            matTooltipPosition="right">
            <mat-icon>{{ collapsed ? 'keyboard_double_arrow_right' : 'keyboard_double_arrow_left' }}</mat-icon>
          </button>
        </div>

        <div class="workspace-switch" *ngIf="!collapsed">
          <button
            type="button"
            class="workspace-button"
            [class.active]="workspace() === 'operate'"
            (click)="switchWorkspace('operate')">
            Operate
          </button>
          <button
            type="button"
            class="workspace-button"
            [class.active]="workspace() === 'setup'"
            (click)="switchWorkspace('setup')">
            Setup
          </button>
        </div>

        <nav class="sidebar-nav">
          <a
            class="nav-item nav-item-dashboard"
            routerLink="/dashboard"
            routerLinkActive="active"
            [routerLinkActiveOptions]="{ exact: true }"
            [matTooltip]="collapsed ? 'Dashboard' : ''"
            matTooltipPosition="right">
            <mat-icon class="nav-icon">dashboard</mat-icon>
            <span class="nav-label" *ngIf="!collapsed">Dashboard</span>
          </a>

          <ng-container *ngFor="let section of visibleSections()">
            <div class="nav-section">
              <div class="nav-section-label" *ngIf="!collapsed">{{ section.label }}</div>

              <a
                class="nav-item"
                *ngFor="let item of section.items"
                [routerLink]="item.route"
                routerLinkActive="active"
                [routerLinkActiveOptions]="item.exact ? { exact: true } : { exact: false }"
                [matTooltip]="collapsed ? item.label : ''"
                matTooltipPosition="right">
                <mat-icon class="nav-icon">{{ item.icon }}</mat-icon>
                <span class="nav-label" *ngIf="!collapsed">{{ item.label }}</span>
                <span class="nav-badge" *ngIf="!collapsed && item.badge">{{ item.badge }}</span>
              </a>
            </div>
          </ng-container>
        </nav>

        <div class="sidebar-bottom">
          <div class="account-divider"></div>

          <div class="meta-pills" *ngIf="!collapsed && currentFacility()">
            <div class="meta-pill">
              <mat-icon>apartment</mat-icon>
              <span>{{ currentFacility()?.code }}</span>
            </div>
            <div class="meta-pill meta-pill-soft">
              <mat-icon>warehouse</mat-icon>
              <span>{{ currentFacility()?.warehouse_key }}</span>
            </div>
          </div>

          <div class="account-label" *ngIf="!collapsed">Account</div>

          <a
            class="nav-item"
            routerLink="/facility-select"
            routerLinkActive="active"
            [matTooltip]="collapsed ? 'Facilities' : ''"
            matTooltipPosition="right">
            <mat-icon class="nav-icon">domain</mat-icon>
            <span class="nav-label" *ngIf="!collapsed">Facilities</span>
            <span class="nav-badge" *ngIf="!collapsed">{{ availableFacilitiesCount() }}</span>
          </a>

          <button
            type="button"
            class="nav-item nav-item-button"
            (click)="onLogout()"
            [matTooltip]="collapsed ? 'Logout' : ''"
            matTooltipPosition="right">
            <mat-icon class="nav-icon">logout</mat-icon>
            <span class="nav-label" *ngIf="!collapsed">Logout</span>
          </button>

          <div class="profile-card" [class.profile-card-collapsed]="collapsed">
            <div class="avatar-shell">
              <img *ngIf="userPhotoUrl()" [src]="userPhotoUrl()!" [alt]="userName()" class="avatar-image">
              <span *ngIf="!userPhotoUrl()" class="avatar-fallback">{{ userInitials() }}</span>
            </div>

            <div class="profile-copy" *ngIf="!collapsed">
              <div class="profile-name">{{ userName() }}</div>
              <div class="profile-subtitle">{{ profileSubtitle() }}</div>
            </div>

            <mat-icon class="profile-more" *ngIf="!collapsed">more_horiz</mat-icon>
          </div>
        </div>
      </div>
    </aside>
  `,
  styles: []
})
export class SidebarComponent {
  @Input() collapsed = false;
  @Output() toggleCollapse = new EventEmitter<void>();

  private auth = inject(AuthService);
  private router = inject(Router);

  readonly workspace = signal<WorkspaceMode>('operate');

  readonly operateSections: NavSection[] = [
    {
      label: 'Transactions',
      items: [
        { label: 'All Transactions', icon: 'receipt_long', route: '/transactions' },
        { label: 'GRN Receive', icon: 'input', route: '/transactions/grn' },
        { label: 'Move Stock', icon: 'swap_horiz', route: '/transactions/move' },
        { label: 'Putaway', icon: 'move_to_inbox', route: '/transactions/putaway' },
        { label: 'Order Pick', icon: 'shopping_cart', route: '/transactions/order-pick' }
      ]
    },
    {
      label: 'Inventory',
      items: [
        { label: 'Stock Balances', icon: 'inventory', route: '/inventory' }
      ]
    }
  ];

  readonly setupSections: NavSection[] = [
    {
      label: 'Masters',
      items: [
        { label: 'SKUs', icon: 'inventory_2', route: '/masters/sku' },
        { label: 'Zones', icon: 'grid_view', route: '/masters/zone' },
        { label: 'Locations', icon: 'location_on', route: '/masters/location' }
      ]
    },
    {
      label: 'Integrations',
      items: [
        { label: 'Connectors', icon: 'hub', route: '/connectors' }
      ]
    }
  ];

  readonly visibleSections = computed(() =>
    this.workspace() === 'operate' ? this.operateSections : this.setupSections
  );

  readonly availableFacilitiesCount = computed(() => this.auth.availableFacilities().length);
  readonly currentFacility = computed(() => this.auth.currentFacility());
  readonly userName = computed(() => this.auth.currentUser()?.display_name?.trim() || 'Warehouse User');
  readonly userEmail = computed(() => this.auth.currentUser()?.email || 'ops@yeswms.local');
  readonly userPhotoUrl = computed(() => this.auth.currentUser()?.photo_url || null);
  readonly profileSubtitle = computed(() => this.currentFacility()?.name || this.userEmail());
  readonly userInitials = computed(() => {
    const parts = this.userName().split(/\s+/).filter(Boolean);
    return (parts[0]?.[0] ?? '?').concat(parts[1]?.[0] ?? '').toUpperCase();
  });

  constructor() {
    this.syncWorkspace(this.router.url);
    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event) => this.syncWorkspace(event.urlAfterRedirects));
  }

  switchWorkspace(mode: WorkspaceMode): void {
    this.workspace.set(mode);

    if (mode === 'operate' && this.isSetupRoute(this.router.url)) {
      this.router.navigate(['/dashboard']);
      return;
    }

    if (mode === 'setup' && !this.isSetupRoute(this.router.url)) {
      this.router.navigate(['/masters/sku']);
    }
  }

  onLogout(): void {
    this.auth.logout();
  }

  private syncWorkspace(url: string): void {
    this.workspace.set(this.isSetupRoute(url) ? 'setup' : 'operate');
  }

  private isSetupRoute(url: string): boolean {
    return url.startsWith('/masters') || url.startsWith('/connectors');
  }
}

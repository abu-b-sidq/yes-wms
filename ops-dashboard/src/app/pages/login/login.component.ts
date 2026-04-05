import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatMenuModule } from '@angular/material/menu';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuthService } from '../../core/auth/auth.service';
import { ThemePreference, ThemeService } from '../../core/services/theme.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatProgressSpinnerModule, MatDividerModule,
    MatMenuModule, MatSnackBarModule, MatTooltipModule
  ],
  template: `
    <div class="login-page" data-scene="login">
      <button mat-icon-button class="theme-fab"
              [matMenuTriggerFor]="themeMenu"
              aria-label="Theme menu"
              [matTooltip]="themeTooltip">
        <mat-icon>{{ themeIcon }}</mat-icon>
      </button>

      <mat-menu #themeMenu="matMenu">
        <div class="menu-header">Theme</div>
        <mat-divider></mat-divider>
        <button mat-menu-item (click)="setTheme('system')" [class.active-theme]="theme.preference() === 'system'">
          <mat-icon>brightness_auto</mat-icon>
          <span>System</span>
        </button>
        <button mat-menu-item (click)="setTheme('light')" [class.active-theme]="theme.preference() === 'light'">
          <mat-icon>light_mode</mat-icon>
          <span>Light</span>
        </button>
        <button mat-menu-item (click)="setTheme('dark')" [class.active-theme]="theme.preference() === 'dark'">
          <mat-icon>dark_mode</mat-icon>
          <span>Dark</span>
        </button>
      </mat-menu>

      <div class="login-stage">
        <section class="login-hero">
          <div class="hero-copy">
            <div class="hero-eyebrow">Smart Warehouse Control</div>
            <h2 class="hero-title">See every carton, conveyor, robot, and handoff from one login.</h2>
            <p class="hero-text">
              Real-time receiving, movement, picking, and dispatch orchestration for high-throughput warehouse teams.
            </p>
            <div class="hero-pills">
              <span class="hero-pill">Inbound visibility</span>
              <span class="hero-pill">Flow orchestration</span>
              <span class="hero-pill">Live operations</span>
            </div>
          </div>
        </section>

        <div class="login-card">
          <!-- Logo -->
          <div class="login-logo">
            <div class="logo-circle">
              <mat-icon>warehouse</mat-icon>
            </div>
            <h1 class="app-name">YES WMS</h1>
            <p class="app-tagline">Operations Dashboard</p>
          </div>

          <!-- Form -->
          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="login-form">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Email</mat-label>
              <mat-icon matPrefix>email</mat-icon>
              <input matInput type="email" formControlName="email"
                     placeholder="you@example.com" autocomplete="username">
              <mat-error *ngIf="form.get('email')?.hasError('required')">Email is required</mat-error>
              <mat-error *ngIf="form.get('email')?.hasError('email')">Invalid email</mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Password</mat-label>
              <mat-icon matPrefix>lock</mat-icon>
              <input matInput [type]="showPassword() ? 'text' : 'password'"
                     formControlName="password" autocomplete="current-password">
              <button mat-icon-button matSuffix type="button"
                      (click)="showPassword.set(!showPassword())">
                <mat-icon>{{ showPassword() ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
              <mat-error *ngIf="form.get('password')?.hasError('required')">Password is required</mat-error>
            </mat-form-field>

            <!-- Error message -->
            <div class="error-banner" *ngIf="errorMsg()">
              <mat-icon>error_outline</mat-icon>
              <span>{{ errorMsg() }}</span>
            </div>

            <button mat-flat-button color="primary" type="submit"
                    class="login-btn" [disabled]="loading()">
              <mat-spinner diameter="20" *ngIf="loading()"></mat-spinner>
              <span *ngIf="!loading()">Sign In</span>
            </button>
          </form>

          <div class="divider-row">
            <mat-divider></mat-divider>
            <span class="divider-text">or</span>
            <mat-divider></mat-divider>
          </div>

          <!-- Google Sign In -->
          <button mat-stroked-button class="google-btn" (click)="onGoogleLogin()" [disabled]="loading()">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                 alt="Google" width="18" height="18">
            Continue with Google
          </button>
        </div>
      </div>
    </div>
  `,
  styles: []
})
export class LoginComponent {
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private fb = inject(FormBuilder);
  theme = inject(ThemeService);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  loading = signal(false);
  showPassword = signal(false);
  errorMsg = signal('');

  get themeIcon(): string {
    const preference = this.theme.preference();
    if (preference === 'light') return 'light_mode';
    if (preference === 'dark') return 'dark_mode';
    return 'brightness_auto';
  }

  get themeTooltip(): string {
    const preference = this.theme.preference();
    if (preference === 'light') return 'Theme: Light';
    if (preference === 'dark') return 'Theme: Dark';
    return 'Theme: System';
  }

  setTheme(preference: ThemePreference): void {
    this.theme.set(preference);
  }

  async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.errorMsg.set('');
    try {
      const { email, password } = this.form.value;
      await this.auth.loginWithEmail(email!, password!);
    } catch (err: unknown) {
      const msg = this.parseFirebaseError(err);
      this.errorMsg.set(msg);
    } finally {
      this.loading.set(false);
    }
  }

  async onGoogleLogin(): Promise<void> {
    this.loading.set(true);
    this.errorMsg.set('');
    try {
      await this.auth.loginWithGoogle();
    } catch (err: unknown) {
      const msg = this.parseFirebaseError(err);
      this.errorMsg.set(msg);
    } finally {
      this.loading.set(false);
    }
  }

  private parseFirebaseError(err: unknown): string {
    if (err && typeof err === 'object' && 'code' in err) {
      const code = (err as { code: string }).code;
      const messages: Record<string, string> = {
        'auth/user-not-found': 'No account found with this email.',
        'auth/wrong-password': 'Incorrect password.',
        'auth/invalid-credential': 'Invalid email or password.',
        'auth/too-many-requests': 'Too many attempts. Please try again later.',
        'auth/network-request-failed': 'Network error. Check your connection.'
      };
      return messages[code] ?? 'Sign in failed. Please try again.';
    }
    return 'Sign in failed. Please try again.';
  }
}

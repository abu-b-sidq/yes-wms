import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatProgressSpinnerModule, MatDividerModule, MatSnackBarModule
  ],
  template: `
    <div class="login-page">
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
  `,
  styles: [`
    .login-page {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
      padding: 16px;
    }
    .login-card {
      background: white;
      border-radius: 20px;
      padding: 40px 32px;
      width: 100%;
      max-width: 400px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    .login-logo {
      text-align: center;
      margin-bottom: 32px;
    }
    .logo-circle {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;
      box-shadow: 0 8px 24px rgba(59,130,246,0.4);
    }
    .logo-circle mat-icon {
      color: white;
      font-size: 32px;
      width: 32px;
      height: 32px;
    }
    .app-name {
      font-size: 28px;
      font-weight: 800;
      color: #1e293b;
      margin: 0 0 4px;
      letter-spacing: -0.5px;
    }
    .app-tagline {
      font-size: 14px;
      color: #64748b;
      margin: 0;
    }
    .login-form {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .full-width { width: 100%; }
    .error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 8px;
      padding: 10px 12px;
      color: #ef4444;
      font-size: 14px;
    }
    .error-banner mat-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
    }
    .login-btn {
      height: 48px;
      font-size: 16px;
      font-weight: 600;
      border-radius: 10px;
      margin-top: 8px;
    }
    .divider-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 20px 0;
    }
    .divider-row mat-divider { flex: 1; }
    .divider-text {
      font-size: 13px;
      color: #94a3b8;
      flex-shrink: 0;
    }
    .google-btn {
      width: 100%;
      height: 48px;
      gap: 10px;
      border-radius: 10px;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  `]
})
export class LoginComponent {
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  loading = signal(false);
  showPassword = signal(false);
  errorMsg = signal('');

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

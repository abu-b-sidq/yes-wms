import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <div class="confirm-dialog">
      <div class="confirm-icon" [class.danger]="data.danger">
        <mat-icon>{{ data.danger ? 'warning' : 'help_outline' }}</mat-icon>
      </div>
      <h2 mat-dialog-title>{{ data.title }}</h2>
      <mat-dialog-content>
        <p>{{ data.message }}</p>
      </mat-dialog-content>
      <mat-dialog-actions>
        <button mat-stroked-button (click)="onCancel()">
          {{ data.cancelLabel ?? 'Cancel' }}
        </button>
        <button mat-flat-button [color]="data.danger ? 'warn' : 'primary'" (click)="onConfirm()">
          {{ data.confirmLabel ?? 'Confirm' }}
        </button>
      </mat-dialog-actions>
    </div>
  `,
  styles: [`
    .confirm-dialog {
      padding: 16px;
      text-align: center;
      max-width: 360px;
      color: var(--ops-text);
    }
    .confirm-icon {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: var(--ops-primary-soft);
      border: 1px solid var(--ops-border);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;
    }
    .confirm-icon mat-icon {
      color: var(--ops-primary);
      font-size: 28px;
      width: 28px;
      height: 28px;
    }
    .confirm-icon.danger {
      background: var(--ops-danger-soft);
    }
    .confirm-icon.danger mat-icon {
      color: var(--ops-danger);
    }
    h2 {
      font-size: 18px;
      font-weight: 600;
      color: var(--ops-text);
      margin: 0 0 8px;
    }
    p {
      color: var(--ops-text-muted);
      margin: 0;
      font-size: 14px;
    }
    mat-dialog-actions {
      justify-content: center;
      gap: 12px;
      padding-top: 16px;
    }
  `]
})
export class ConfirmDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ConfirmDialogData
  ) {}

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }
}

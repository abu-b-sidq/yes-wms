import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormArray, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../../core/services/operations.service';
import { MastersService } from '../../../core/services/masters.service';
import { Sku, Location } from '../../../core/models/masters.model';
import { Transaction } from '../../../core/models/operations.model';

@Component({
  selector: 'app-move',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSnackBarModule,
    MatProgressSpinnerModule, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="Move Stock" description="Transfer stock between locations" icon="swap_horiz">
      </app-page-header>

      <!-- Success state -->
      <div class="success-card" *ngIf="successTxn()">
        <div class="success-icon"><mat-icon>check_circle</mat-icon></div>
        <h3>Move Executed</h3>
        <p>Transaction ID: <span class="mono">{{ successTxn()!.id.slice(0,8) }}...</span></p>
        <p>Status: <span class="badge completed">{{ successTxn()!.status }}</span></p>
        <div class="success-actions">
          <button mat-stroked-button (click)="resetForm()">New Move</button>
          <button mat-flat-button color="primary" (click)="router.navigate(['/transactions'])">View Transactions</button>
        </div>
      </div>

      <div class="form-area" *ngIf="!successTxn()">
        <form [formGroup]="form" (ngSubmit)="onSubmit()">

          <div class="form-card">
            <div class="card-title">Transaction Details</div>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Reference (Optional)</mat-label>
              <input matInput formControlName="reference">
            </mat-form-field>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Notes (Optional)</mat-label>
              <textarea matInput formControlName="notes" rows="2"></textarea>
            </mat-form-field>
          </div>

          <div class="form-card">
            <div class="card-title-row">
              <div class="card-title">Move Lines</div>
              <button mat-stroked-button type="button" (click)="addItem()">
                <mat-icon>add</mat-icon> Add Line
              </button>
            </div>

            <div formArrayName="items">
              <div class="move-line" *ngFor="let item of items.controls; let i = index" [formGroupName]="i">
                <div class="line-header">
                  <span class="line-num">Line {{ i + 1 }}</span>
                  <button mat-icon-button type="button" color="warn" (click)="removeItem(i)" [disabled]="items.length === 1">
                    <mat-icon>delete</mat-icon>
                  </button>
                </div>
                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>SKU *</mat-label>
                  <mat-select formControlName="sku_code">
                    <mat-option *ngFor="let sku of skus()" [value]="sku.code">{{ sku.code }} — {{ sku.name }}</mat-option>
                  </mat-select>
                  <mat-error>Required</mat-error>
                </mat-form-field>
                <div class="row-2">
                  <mat-form-field appearance="outline" class="flex-1">
                    <mat-label>From Location *</mat-label>
                    <mat-select formControlName="source_location">
                      <mat-option *ngFor="let loc of locations()" [value]="loc.code">{{ loc.code }} — {{ loc.name }}</mat-option>
                    </mat-select>
                    <mat-error>Required</mat-error>
                  </mat-form-field>
                  <mat-icon class="arrow-icon">arrow_forward</mat-icon>
                  <mat-form-field appearance="outline" class="flex-1">
                    <mat-label>To Location *</mat-label>
                    <mat-select formControlName="destination_location">
                      <mat-option *ngFor="let loc of locations()" [value]="loc.code">{{ loc.code }} — {{ loc.name }}</mat-option>
                    </mat-select>
                    <mat-error>Required</mat-error>
                  </mat-form-field>
                </div>
                <div class="row-2">
                  <mat-form-field appearance="outline" style="flex: 0 0 120px">
                    <mat-label>Qty *</mat-label>
                    <input matInput type="number" formControlName="quantity" min="1">
                    <mat-error>Min 1</mat-error>
                  </mat-form-field>
                  <mat-form-field appearance="outline" class="flex-1">
                    <mat-label>Batch (Optional)</mat-label>
                    <input matInput formControlName="batch">
                  </mat-form-field>
                </div>
              </div>
            </div>
          </div>

          <div class="submit-area">
            <button mat-flat-button color="primary" type="submit" class="submit-btn" [disabled]="submitting()">
              <mat-spinner diameter="20" *ngIf="submitting()"></mat-spinner>
              <mat-icon *ngIf="!submitting()">swap_horiz</mat-icon>
              {{ submitting() ? 'Executing...' : 'Execute Move' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .form-area { padding: 0 24px 24px; }
    .form-card {
      background: white; border-radius: 12px; padding: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px;
    }
    .card-title { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
    .card-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
    .full-width { width: 100%; }
    .move-line {
      background: #f8fafc; border-radius: 10px; padding: 12px;
      margin-bottom: 12px; display: flex; flex-direction: column; gap: 4px;
    }
    .line-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
    .line-num { font-size: 13px; font-weight: 600; color: #3b82f6; }
    .row-2 { display: flex; gap: 8px; align-items: center; }
    .flex-1 { flex: 1; }
    .arrow-icon { color: #94a3b8; flex-shrink: 0; }
    .submit-area { display: flex; justify-content: flex-end; }
    .submit-btn { height: 48px; padding: 0 32px; font-size: 15px; font-weight: 600; gap: 8px; }
    .success-card {
      margin: 0 24px 24px; background: white; border-radius: 16px;
      padding: 40px 24px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .success-icon mat-icon { font-size: 64px; width: 64px; height: 64px; color: #16a34a; }
    h3 { font-size: 20px; font-weight: 700; color: #1e293b; margin: 16px 0 8px; }
    p { color: #64748b; margin: 4px 0; }
    .mono { font-family: monospace; font-size: 13px; }
    .badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
    .badge.completed { background: #dcfce7; color: #16a34a; }
    .success-actions { display: flex; gap: 12px; justify-content: center; margin-top: 24px; }
    @media (max-width: 600px) {
      .form-area { padding: 0 12px 16px; }
      .row-2 { flex-direction: column; }
      .arrow-icon { transform: rotate(90deg); }
    }
  `]
})
export class MoveComponent implements OnInit {
  router = inject(Router);
  private ops = inject(OperationsService);
  private masters = inject(MastersService);
  private snack = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  skus = signal<Sku[]>([]);
  locations = signal<Location[]>([]);
  submitting = signal(false);
  successTxn = signal<Transaction | null>(null);

  form = this.fb.group({
    reference: [''],
    notes: [''],
    items: this.fb.array([this.createItem()])
  });

  get items() { return this.form.get('items') as FormArray; }

  createItem() {
    return this.fb.group({
      sku_code: ['', Validators.required],
      quantity: [1, [Validators.required, Validators.min(1)]],
      source_location: ['', Validators.required],
      destination_location: ['', Validators.required],
      batch: ['']
    });
  }

  addItem() { this.items.push(this.createItem()); }
  removeItem(i: number) { this.items.removeAt(i); }

  ngOnInit(): void {
    this.masters.getSkus({ size: 500 }).subscribe(res => this.skus.set(Array.isArray(res) ? res : res.items));
    this.masters.getLocations({ size: 500 }).subscribe(res => this.locations.set(Array.isArray(res) ? res : res.items));
  }

  onSubmit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.submitting.set(true);
    const val = this.form.value;
    this.ops.createMove({
      reference: val.reference || undefined,
      notes: val.notes || undefined,
      items: (val.items ?? []).map((i: any) => ({
        sku_code: i.sku_code, quantity: Number(i.quantity),
        source_location: i.source_location, destination_location: i.destination_location,
        batch: i.batch || undefined
      }))
    }).subscribe({
      next: (txn) => { this.successTxn.set(txn); this.submitting.set(false); },
      error: (err) => {
        this.snack.open(err?.error?.detail ?? 'Failed to execute move', 'Dismiss', { duration: 5000 });
        this.submitting.set(false);
      }
    });
  }

  resetForm(): void {
    this.successTxn.set(null);
    this.form.reset();
    while (this.items.length > 1) this.items.removeAt(1);
    this.items.at(0).patchValue({ quantity: 1 });
  }
}

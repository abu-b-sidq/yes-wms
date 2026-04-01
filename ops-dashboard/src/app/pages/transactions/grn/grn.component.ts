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
import { MatDividerModule } from '@angular/material/divider';
import { PageHeaderComponent } from '../../../shared/components/page-header/page-header.component';
import { OperationsService } from '../../../core/services/operations.service';
import { MastersService } from '../../../core/services/masters.service';
import { Sku, Zone } from '../../../core/models/masters.model';
import { Transaction } from '../../../core/models/operations.model';

@Component({
  selector: 'app-grn',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatSelectModule, MatSnackBarModule,
    MatProgressSpinnerModule, MatDividerModule, PageHeaderComponent
  ],
  template: `
    <div class="page-container">
      <app-page-header title="GRN — Goods Receipt" description="Receive goods into the warehouse" icon="input">
      </app-page-header>

      <!-- Success state -->
      <div class="success-card" *ngIf="successTxn()">
        <div class="success-icon">
          <mat-icon>check_circle</mat-icon>
        </div>
        <h3>GRN Created & Executed</h3>
        <p>Transaction ID: <span class="mono">{{ successTxn()!.id.slice(0,8) }}...</span></p>
        <p>Status: <span class="badge completed">{{ successTxn()!.status }}</span></p>
        <div class="success-actions">
          <button mat-stroked-button (click)="resetForm()">New GRN</button>
          <button mat-flat-button color="primary" (click)="goToTransactions()">View Transactions</button>
        </div>
      </div>

      <!-- GRN Form -->
      <div class="form-area" *ngIf="!successTxn()">
        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="grn-form">

          <!-- Header -->
          <div class="form-card">
            <div class="card-title">Transaction Details</div>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Reference (Optional)</mat-label>
              <mat-icon matPrefix>tag</mat-icon>
              <input matInput formControlName="reference" placeholder="e.g. PO-2024-001">
            </mat-form-field>
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Notes (Optional)</mat-label>
              <textarea matInput formControlName="notes" rows="2" placeholder="Any notes..."></textarea>
            </mat-form-field>
          </div>

          <!-- Items -->
          <div class="form-card">
            <div class="card-title-row">
              <div class="card-title">Items to Receive</div>
              <button mat-stroked-button type="button" (click)="addItem()">
                <mat-icon>add</mat-icon> Add Item
              </button>
            </div>

            <div class="items-list" formArrayName="items">
              <div class="item-row" *ngFor="let item of items.controls; let i = index" [formGroupName]="i">
                <div class="item-number">{{ i + 1 }}</div>
                <div class="item-fields">
                  <mat-form-field appearance="outline" class="full-width">
                    <mat-label>SKU *</mat-label>
                    <mat-select formControlName="sku_code">
                      <mat-option *ngFor="let sku of skus()" [value]="sku.code">
                        {{ sku.code }} — {{ sku.name }}
                      </mat-option>
                    </mat-select>
                    <mat-error>Required</mat-error>
                  </mat-form-field>
                  <div class="item-row-2">
                    <mat-form-field appearance="outline" class="qty-field">
                      <mat-label>Qty *</mat-label>
                      <input matInput type="number" formControlName="quantity" min="1">
                      <mat-error>Min 1</mat-error>
                    </mat-form-field>
                    <mat-form-field appearance="outline" class="batch-field">
                      <mat-label>Batch (Optional)</mat-label>
                      <input matInput formControlName="batch" placeholder="Batch no.">
                    </mat-form-field>
                  </div>
                  <mat-form-field appearance="outline" class="full-width">
                    <mat-label>Destination Zone (Optional)</mat-label>
                    <mat-select formControlName="destination_zone">
                      <mat-option value="">— Default (PRE_PUTAWAY) —</mat-option>
                      <mat-option *ngFor="let z of zones()" [value]="z.code">
                        {{ z.name }} ({{ z.code }})
                      </mat-option>
                    </mat-select>
                  </mat-form-field>
                </div>
                <button mat-icon-button type="button" color="warn"
                        (click)="removeItem(i)" [disabled]="items.length === 1">
                  <mat-icon>delete</mat-icon>
                </button>
              </div>
            </div>

            <!-- Total -->
            <div class="totals-row">
              <span class="totals-label">Total Items: <strong>{{ items.length }}</strong></span>
              <span class="totals-label">Total Qty: <strong>{{ totalQty }}</strong></span>
            </div>
          </div>

          <!-- Submit -->
          <div class="submit-area">
            <button mat-flat-button color="primary" type="submit"
                    class="submit-btn" [disabled]="submitting()">
              <mat-spinner diameter="20" *ngIf="submitting()"></mat-spinner>
              <mat-icon *ngIf="!submitting()">check</mat-icon>
              {{ submitting() ? 'Creating GRN...' : 'Create & Execute GRN' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .page-container { min-height: 100%; }
    .form-area { padding: 0 24px 24px; }
    .grn-form { display: flex; flex-direction: column; gap: 16px; }
    .form-card {
      background: white;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .card-title {
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 8px;
    }
    .card-title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .full-width { width: 100%; }
    .items-list { display: flex; flex-direction: column; gap: 12px; }
    .item-row {
      display: flex;
      gap: 8px;
      align-items: flex-start;
      background: #f8fafc;
      border-radius: 10px;
      padding: 12px;
    }
    .item-number {
      width: 24px;
      height: 24px;
      background: #3b82f6;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 700;
      flex-shrink: 0;
      margin-top: 12px;
    }
    .item-fields { flex: 1; display: flex; flex-direction: column; gap: 4px; }
    .item-row-2 { display: flex; gap: 8px; }
    .qty-field { flex: 0 0 120px; }
    .batch-field { flex: 1; }
    .totals-row {
      display: flex;
      gap: 24px;
      padding: 12px 0 4px;
      border-top: 1px solid #f1f5f9;
      margin-top: 4px;
    }
    .totals-label { font-size: 13px; color: #64748b; }
    .submit-area { display: flex; justify-content: flex-end; }
    .submit-btn {
      height: 48px;
      padding: 0 32px;
      font-size: 15px;
      font-weight: 600;
      gap: 8px;
    }
    .success-card {
      margin: 0 24px 24px;
      background: white;
      border-radius: 16px;
      padding: 40px 24px;
      text-align: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .success-icon mat-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      color: #16a34a;
    }
    h3 { font-size: 20px; font-weight: 700; color: #1e293b; margin: 16px 0 8px; }
    p { color: #64748b; margin: 4px 0; }
    .mono { font-family: monospace; font-size: 13px; }
    .badge { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 20px; }
    .badge.completed { background: #dcfce7; color: #16a34a; }
    .success-actions { display: flex; gap: 12px; justify-content: center; margin-top: 24px; }
    @media (max-width: 600px) {
      .form-area { padding: 0 12px 16px; }
      .item-row-2 { flex-direction: column; }
      .qty-field { flex: none; }
    }
  `]
})
export class GrnComponent implements OnInit {
  private ops = inject(OperationsService);
  private masters = inject(MastersService);
  private snack = inject(MatSnackBar);
  private router = inject(Router);
  private fb = inject(FormBuilder);

  skus = signal<Sku[]>([]);
  zones = signal<Zone[]>([]);
  submitting = signal(false);
  successTxn = signal<Transaction | null>(null);

  form = this.fb.group({
    reference: [''],
    notes: [''],
    items: this.fb.array([this.createItem()])
  });

  get items() { return this.form.get('items') as FormArray; }
  get totalQty() {
    return this.items.controls.reduce((sum, c) => sum + (Number(c.get('quantity')?.value) || 0), 0);
  }

  createItem() {
    return this.fb.group({
      sku_code: ['', Validators.required],
      quantity: [1, [Validators.required, Validators.min(1)]],
      batch: [''],
      destination_zone: ['']
    });
  }

  addItem() { this.items.push(this.createItem()); }
  removeItem(i: number) { this.items.removeAt(i); }

  ngOnInit(): void {
    this.masters.getSkus({ size: 500 }).subscribe(res => {
      this.skus.set(Array.isArray(res) ? res : res.items);
    });
    this.masters.getZones({ size: 200 }).subscribe(res => {
      this.zones.set(Array.isArray(res) ? res : res.items);
    });
  }

  onSubmit(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.submitting.set(true);
    const val = this.form.value;
    this.ops.createGrn({
      reference: val.reference || undefined,
      notes: val.notes || undefined,
      items: (val.items ?? []).map((item: any) => ({
        sku_code: item.sku_code,
        quantity: Number(item.quantity),
        batch: item.batch || undefined,
        destination_zone: item.destination_zone || undefined
      }))
    }).subscribe({
      next: (txn) => {
        this.successTxn.set(txn);
        this.submitting.set(false);
      },
      error: (err) => {
        const msg = err?.error?.detail ?? 'Failed to create GRN';
        this.snack.open(msg, 'Dismiss', { duration: 5000 });
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

  goToTransactions(): void { this.router.navigate(['/transactions']); }
}

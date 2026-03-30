import { Injectable, signal, computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import {
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User as FirebaseUser,
  GoogleAuthProvider,
  signInWithPopup
} from 'firebase/auth';
import { getFirebaseAuth } from './firebase.config';
import { AppUser, Facility, SessionLoginResponse, WmsSession } from '../models/user.model';
import { environment } from '../../../environments/environment';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  private _session = signal<WmsSession | null>(null);
  private _loading = signal(true);
  private _firebaseUser = signal<FirebaseUser | null>(null);
  private _availableFacilities = signal<Facility[]>([]);

  readonly session = computed(() => this._session());
  readonly loading = computed(() => this._loading());
  readonly isAuthenticated = computed(() => this._session() !== null);
  readonly currentUser = computed(() => this._session()?.user ?? null);
  readonly currentFacility = computed(() => this._session()?.facility ?? null);
  readonly availableFacilities = computed(() => this._availableFacilities());
  readonly permissions = computed(() => this._session()?.permissions ?? []);

  constructor() {
    this.initAuthState();
  }

  private initAuthState(): void {
    const auth = getFirebaseAuth();
    if (!auth) {
      this._loading.set(false);
      return;
    }
    onAuthStateChanged(auth, async (firebaseUser) => {
      this._firebaseUser.set(firebaseUser);
      if (firebaseUser) {
        await this.restoreSession(firebaseUser);
      } else {
        this._session.set(null);
        this._availableFacilities.set([]);
      }
      this._loading.set(false);
    });
  }

  private async restoreSession(firebaseUser: FirebaseUser): Promise<void> {
    const saved = localStorage.getItem('wms_session');
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as WmsSession;
        this._session.set(parsed);
        await this.loadMobileSessions(firebaseUser);
      } catch {
        localStorage.removeItem('wms_session');
        await this.loadMobileSessions(firebaseUser);
      }
    } else {
      await this.loadMobileSessions(firebaseUser);
    }
  }

  private async loadMobileSessions(firebaseUser: FirebaseUser): Promise<void> {
    try {
      const token = await firebaseUser.getIdToken();
      const response = await firstValueFrom(
        this.http.post<SessionLoginResponse>(
          `${environment.apiUrl}/operations/mobile/session/login`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        )
      );
      this._availableFacilities.set(response.available_facilities);
      // Auto-select last used facility or first available
      const facility = response.last_used_facility ?? response.available_facilities[0] ?? null;
      if (facility && !this._session()) {
        await this.selectFacility(facility, response.user, token);
      } else if (!facility) {
        // No facilities — keep session null but store user for display
        this._session.set(null);
      }
    } catch {
      // If mobile session endpoint fails, clear session
      this._session.set(null);
    }
  }

  async loginWithEmail(email: string, password: string): Promise<void> {
    const auth = getFirebaseAuth();
    const credential = await signInWithEmailAndPassword(auth, email, password);
    const token = await credential.user.getIdToken();
    await this.loadMobileSessions(credential.user);
    if (!this._session() && this._availableFacilities().length > 0) {
      this.router.navigate(['/facility-select']);
    }
  }

  async loginWithGoogle(): Promise<void> {
    const auth = getFirebaseAuth();
    const provider = new GoogleAuthProvider();
    const credential = await signInWithPopup(auth, provider);
    const token = await credential.user.getIdToken();
    await this.loadMobileSessions(credential.user);
    if (!this._session() && this._availableFacilities().length > 0) {
      this.router.navigate(['/facility-select']);
    }
  }

  async selectFacility(facility: Facility, user?: AppUser, existingToken?: string): Promise<void> {
    const firebaseUser = this._firebaseUser();
    if (!firebaseUser) return;

    const token = existingToken ?? await firebaseUser.getIdToken();

    // Notify backend about facility selection
    try {
      await firstValueFrom(
        this.http.post(
          `${environment.apiUrl}/operations/mobile/session/select-facility`,
          { facility_id: facility.id },
          { headers: { Authorization: `Bearer ${token}`, warehouse: facility.warehouse_key } }
        )
      );
    } catch {
      // Non-blocking — continue
    }

    const appUser = user ?? this._session()?.user ?? {
      id: firebaseUser.uid,
      email: firebaseUser.email ?? '',
      display_name: firebaseUser.displayName ?? firebaseUser.email ?? '',
      status: 'ACTIVE' as const
    };

    const session: WmsSession = {
      user: appUser,
      facility,
      orgId: '', // Will be resolved from facility context
      warehouseKey: facility.warehouse_key,
      permissions: this.resolvePermissionsFromRoles()
    };

    this._session.set(session);
    localStorage.setItem('wms_session', JSON.stringify(session));
    this.router.navigate(['/dashboard']);
  }

  private resolvePermissionsFromRoles(): string[] {
    // Permissions are enforced server-side; client shows UI based on role hints
    // Return all possible permissions — server will reject unauthorized calls
    return [
      'masters.read', 'masters.manage',
      'inventory.read',
      'transactions.read', 'transactions.manage',
      'operations.execute'
    ];
  }

  hasPermission(permission: string): boolean {
    return this.permissions().includes(permission);
  }

  async getToken(): Promise<string | null> {
    const user = this._firebaseUser();
    if (!user) return null;
    return user.getIdToken();
  }

  async logout(): Promise<void> {
    const auth = getFirebaseAuth();
    await signOut(auth);
    this._session.set(null);
    this._availableFacilities.set([]);
    localStorage.removeItem('wms_session');
    this.router.navigate(['/login']);
  }
}

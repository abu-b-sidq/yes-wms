import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { from, switchMap } from 'rxjs';
import { AuthService } from '../auth/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const session = auth.session();

  // Skip non-API requests
  if (!req.url.includes('/api/v1')) {
    return next(req);
  }

  return from(auth.getToken()).pipe(
    switchMap(token => {
      let headers = req.headers;

      if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }

      if (session?.warehouseKey && !headers.has('warehouse')) {
        headers = headers.set('warehouse', session.warehouseKey);
      }

      if (session?.orgId && !headers.has('X-Org-Id')) {
        headers = headers.set('X-Org-Id', session.orgId);
      }

      if (session?.facility?.code && !headers.has('X-Facility-Id')) {
        headers = headers.set('X-Facility-Id', session.facility.code);
      }

      return next(req.clone({ headers }));
    })
  );
};

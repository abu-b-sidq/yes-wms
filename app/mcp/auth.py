"""OAuth2 Authorization Server wrapping Firebase Authentication for MCP."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from urllib.parse import urlencode

from django.core.cache import cache
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from app.auth.firebase_verifier import FirebaseInvalidTokenError, get_firebase_verifier

_CODE_PREFIX = "mcp_oauth_code:"
_CODE_TTL = 300  # 5 minutes


def _base_url(request: Request) -> str:
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    return f"{scheme}://{host}"


async def oauth_metadata(request: Request) -> JSONResponse:
    """GET /.well-known/oauth-authorization-server"""
    base = _base_url(request)
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/mcp/oauth/authorize",
        "token_endpoint": f"{base}/mcp/oauth/token",
        "registration_endpoint": f"{base}/mcp/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    })


async def oauth_register(request: Request) -> JSONResponse:
    """POST /mcp/oauth/register — open dynamic client registration."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    return JSONResponse({
        "client_id": body.get("client_name", "mcp-client"),
        "client_secret_expires_at": 0,
        "redirect_uris": body.get("redirect_uris", []),
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }, status_code=201)


async def oauth_authorize(request: Request) -> HTMLResponse:
    """GET /mcp/oauth/authorize — serve Firebase login page."""
    redirect_uri = request.query_params.get("redirect_uri", "")
    state = request.query_params.get("state", "")
    code_challenge = request.query_params.get("code_challenge", "")
    code_challenge_method = request.query_params.get("code_challenge_method", "S256")

    firebase_api_key = os.getenv("FIREBASE_WEB_API_KEY", "")
    firebase_auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", "")

    # Embed params as JSON to safely escape into JS
    params_json = json.dumps({
        "redirectUri": redirect_uri,
        "state": state,
        "codeChallenge": code_challenge,
        "codeChallengeMethod": code_challenge_method,
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YES WMS — Sign In</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#f5f5f5;display:flex;align-items:center;justify-content:center;min-height:100vh}}
  .card{{background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.08);padding:40px;width:360px}}
  h1{{font-size:22px;font-weight:700;margin-bottom:6px;color:#111}}
  .sub{{color:#666;font-size:14px;margin-bottom:28px}}
  label{{display:block;font-size:13px;color:#444;margin-bottom:4px;font-weight:500}}
  input{{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:14px;outline:none;transition:border .2s}}
  input:focus{{border-color:#4f46e5}}
  .btn{{width:100%;padding:11px;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity .2s}}
  .btn:hover{{opacity:.88}}
  .btn-primary{{background:#4f46e5;color:#fff;margin-bottom:10px}}
  .btn-google{{background:#fff;color:#333;border:1px solid #ddd;display:flex;align-items:center;justify-content:center;gap:8px}}
  .divider{{text-align:center;color:#aaa;font-size:13px;margin:2px 0 10px}}
  .error{{color:#dc2626;font-size:13px;margin-top:10px;display:none;padding:8px 12px;background:#fef2f2;border-radius:6px}}
  .loading{{opacity:.6;pointer-events:none}}
</style>
</head>
<body>
<div class="card">
  <h1>YES WMS</h1>
  <p class="sub">Sign in to connect your AI assistant.</p>

  <form id="form">
    <label>Email</label>
    <input type="email" id="email" placeholder="you@example.com" required autocomplete="email">
    <label>Password</label>
    <input type="password" id="password" placeholder="••••••••" required autocomplete="current-password">
    <button type="submit" class="btn btn-primary" id="submitBtn">Sign in</button>
  </form>

  <div class="divider">or</div>

  <button class="btn btn-google" id="googleBtn">
    <svg width="18" height="18" viewBox="0 0 48 48">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
    </svg>
    Continue with Google
  </button>

  <div class="error" id="errorMsg"></div>
</div>

<script type="module">
  import {{ initializeApp }} from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
  import {{ getAuth, signInWithEmailAndPassword, GoogleAuthProvider, signInWithPopup }}
    from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';

  const PARAMS = {params_json};

  const app = initializeApp({{
    apiKey: "{firebase_api_key}",
    authDomain: "{firebase_auth_domain}",
    projectId: "{firebase_project_id}",
  }});
  const auth = getAuth(app);

  function showError(msg) {{
    const el = document.getElementById('errorMsg');
    el.textContent = msg;
    el.style.display = 'block';
  }}

  function setLoading(on) {{
    document.getElementById('submitBtn').classList.toggle('loading', on);
    document.getElementById('googleBtn').classList.toggle('loading', on);
  }}

  async function handleUser(user) {{
    const idToken = await user.getIdToken();
    const resp = await fetch('/mcp/oauth/callback', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        id_token: idToken,
        redirect_uri: PARAMS.redirectUri,
        state: PARAMS.state,
        code_challenge: PARAMS.codeChallenge,
        code_challenge_method: PARAMS.codeChallengeMethod,
      }}),
    }});
    const data = await resp.json();
    if (data.redirect_to) {{
      window.location.href = data.redirect_to;
    }} else {{
      showError(data.error || 'Authentication failed.');
      setLoading(false);
    }}
  }}

  document.getElementById('form').addEventListener('submit', async (e) => {{
    e.preventDefault();
    setLoading(true);
    document.getElementById('errorMsg').style.display = 'none';
    try {{
      const {{ user }} = await signInWithEmailAndPassword(
        auth,
        document.getElementById('email').value,
        document.getElementById('password').value,
      );
      await handleUser(user);
    }} catch (err) {{
      showError(err.message);
      setLoading(false);
    }}
  }});

  document.getElementById('googleBtn').addEventListener('click', async () => {{
    setLoading(true);
    document.getElementById('errorMsg').style.display = 'none';
    try {{
      const {{ user }} = await signInWithPopup(auth, new GoogleAuthProvider());
      await handleUser(user);
    }} catch (err) {{
      showError(err.message);
      setLoading(false);
    }}
  }});
</script>
</body>
</html>"""
    return HTMLResponse(html)


async def oauth_callback(request: Request) -> JSONResponse:
    """POST /mcp/oauth/callback — receive Firebase ID token, issue one-time auth code."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid_request"}, status_code=400)

    id_token = body.get("id_token", "")
    redirect_uri = body.get("redirect_uri", "")
    state = body.get("state", "")
    code_challenge = body.get("code_challenge", "")
    code_challenge_method = body.get("code_challenge_method", "S256")

    if not id_token:
        return JSONResponse({"error": "missing id_token"}, status_code=400)
    if not redirect_uri:
        return JSONResponse({"error": "missing redirect_uri"}, status_code=400)

    try:
        import asyncio
        await asyncio.to_thread(get_firebase_verifier().verify, id_token)
    except FirebaseInvalidTokenError:
        return JSONResponse({"error": "invalid_token"}, status_code=401)
    except Exception:
        return JSONResponse({"error": "verification_failed"}, status_code=500)

    auth_code = secrets.token_urlsafe(32)
    cache.set(
        f"{_CODE_PREFIX}{auth_code}",
        {
            "id_token": id_token,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        },
        timeout=_CODE_TTL,
    )

    params: dict[str, str] = {"code": auth_code}
    if state:
        params["state"] = state
    sep = "&" if "?" in redirect_uri else "?"
    redirect_to = redirect_uri + sep + urlencode(params)

    return JSONResponse({"redirect_to": redirect_to})


async def oauth_token(request: Request) -> JSONResponse:
    """POST /mcp/oauth/token — exchange auth code for Firebase access token."""
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        body: dict = dict(form)
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}

    grant_type = body.get("grant_type", "")
    if grant_type != "authorization_code":
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)

    code = body.get("code", "")
    code_verifier = body.get("code_verifier", "")

    if not code:
        return JSONResponse(
            {"error": "invalid_request", "error_description": "missing code"},
            status_code=400,
        )

    stored = cache.get(f"{_CODE_PREFIX}{code}")
    if not stored:
        return JSONResponse(
            {"error": "invalid_grant", "error_description": "code not found or expired"},
            status_code=400,
        )

    # PKCE verification
    code_challenge = stored.get("code_challenge", "")
    if code_challenge:
        if not code_verifier:
            return JSONResponse(
                {"error": "invalid_request", "error_description": "missing code_verifier"},
                status_code=400,
            )
        digest = hashlib.sha256(code_verifier.encode()).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        if computed != code_challenge:
            return JSONResponse(
                {"error": "invalid_grant", "error_description": "PKCE verification failed"},
                status_code=400,
            )

    # One-time use: delete the code
    cache.delete(f"{_CODE_PREFIX}{code}")

    return JSONResponse({
        "access_token": stored["id_token"],
        "token_type": "bearer",
        "expires_in": 3600,
    })

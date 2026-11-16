# Authentication flow

Login/register return JWT/user JSON and set a refresh cookie. Page code stores the access token in api.js module memory; JavaScript cannot read the HttpOnly cookie. On reload loadSession requests /users/me; a protected 401 triggers a shared refresh and one retry. requireSession redirects absent identity to /login.html.

loadSession({throwOnUnavailable:true}) can distinguish network/service failure from 401. Default behavior clears identity on caught errors, so not all callers preserve visible session state on outages. apiFetch includes credentials and disables caching.

Successful logout revokes the refresh token, clears access memory and notifies other tabs using localStorage. The assistant aborts work/clears visible history. Conversation pointers are per user but do not authorize access. Failed logout is not proof of server revocation. Password changes revoke refresh sessions; old JWTs last until expiry.

[Section index](README.md) · [Documentation home](../README.md)

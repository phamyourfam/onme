/* ── Auth Store (Svelte 5 Runes) ────────────────────────────────── */

import { login, register, getMe } from '$lib/api';
import type { AuthUser } from '$lib/types';

const TOKEN_KEY = 'onme_token';
const USER_KEY = 'onme_user';

/* ── Reactive state ─────────────────────────────────────────────── */

let token = $state<string | null>(null);
let user = $state<AuthUser | null>(null);
let initialised = $state(false);

/* ── Exported getters (cannot export $derived from modules) ────── */

export function getIsAuthenticated(): boolean {
    return !!token;
}

export function getIsInitialised(): boolean {
    return initialised;
}

export function getAuthUser(): AuthUser | null {
    return user;
}

/* ── Init — restore session from localStorage + hydrate via /me ── */

export async function initAuth(): Promise<void> {
    try {
        const savedToken = localStorage.getItem(TOKEN_KEY);

        if (savedToken) {
            token = savedToken;

            // Hydrate user profile from backend
            try {
                const me = await getMe();
                user = me;
                localStorage.setItem(USER_KEY, JSON.stringify(me));
            } catch {
                // Token is stale or invalid — clear everything
                token = null;
                user = null;
                localStorage.removeItem(TOKEN_KEY);
                localStorage.removeItem(USER_KEY);
            }
        }
    } catch {
        // localStorage not available (SSR fallback)
    }

    // Listen for 401 auto-logout events dispatched by api.ts
    if (typeof window !== 'undefined') {
        window.addEventListener('onme:auth-expired', () => {
            logoutAction();
        });
    }

    initialised = true;
}

/* ── Login ──────────────────────────────────────────────────────── */

export async function loginAction(
    email: string,
    password: string
): Promise<void> {
    const res = await login(email, password);

    token = res.access_token;
    localStorage.setItem(TOKEN_KEY, res.access_token);

    // Hydrate full user profile from /me
    try {
        const me = await getMe();
        user = me;
        localStorage.setItem(USER_KEY, JSON.stringify(me));
    } catch {
        // Fallback: store minimal user info
        const userInfo: AuthUser = {
            id: '',
            email: email,
            credits_remaining: 0
        };
        user = userInfo;
        localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
    }
}

/* ── Register ───────────────────────────────────────────────────── */

export async function registerAction(
    email: string,
    password: string
): Promise<void> {
    const res = await register(email, password);

    token = res.token;
    localStorage.setItem(TOKEN_KEY, res.token);

    const userInfo: AuthUser = {
        id: res.id,
        email: res.email,
        credits_remaining: 10
    };
    user = userInfo;
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
}

/* ── Logout ─────────────────────────────────────────────────────── */

export function logoutAction(): void {
    token = null;
    user = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

/* ── Refresh user data ──────────────────────────────────────────── */

export async function refreshUser(): Promise<void> {
    if (!token) return;

    try {
        const me = await getMe();
        user = me;
        localStorage.setItem(USER_KEY, JSON.stringify(me));
    } catch {
        // Silently fail — user data stays as-is
    }
}

/* ── Auth Store (Svelte 5 Runes) ────────────────────────────────── */

import { login, register, ApiError } from '$lib/api';
import type { AuthUser } from '$lib/types';

const TOKEN_KEY = 'onme_token';
const USER_KEY = 'onme_user';

/* ── Reactive state ─────────────────────────────────────────────── */

let token = $state<string | null>(null);
let user = $state<AuthUser | null>(null);
let initialised = $state(false);

/* ── Derived ────────────────────────────────────────────────────── */

export const isAuthenticated = $derived(!!token);
export const isInitialised = $derived(initialised);
export const authUser = $derived(user);

/* ── Init — restore session from localStorage ───────────────────── */

export function initAuth(): void {
    try {
        const savedToken = localStorage.getItem(TOKEN_KEY);
        const savedUser = localStorage.getItem(USER_KEY);

        if (savedToken) {
            token = savedToken;
        }
        if (savedUser) {
            try {
                user = JSON.parse(savedUser);
            } catch {
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

    // Store basic user info from login (no /auth/me endpoint needed)
    const userInfo: AuthUser = {
        id: '',
        email: email,
        credits_remaining: 0
    };
    user = userInfo;
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
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
        credits_remaining: 0
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

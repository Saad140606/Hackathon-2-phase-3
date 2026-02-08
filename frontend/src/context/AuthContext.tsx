// T020: AuthContext with AuthContextProvider - Updated for BetterAuth

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { User, AuthState, AuthContextType } from '@/types/auth';
import { useBetterAuth } from '@/hooks/useBetterAuth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper function to decode JWT token
function parseJwt(token: string) {
  try {
    if (!token || typeof token !== 'string') return null;
    const parts = token.split('.');
    if (parts.length < 2 || !parts[1]) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );

    return JSON.parse(jsonPayload);
  } catch (error) {
    // Don't throw on invalid tokens; return null so callers treat user as unauthenticated
    console.debug('Error parsing JWT token:', error);
    return null;
  }
}

export function AuthContextProvider({ children }: { children: ReactNode }) {
  const authHook = useBetterAuth();
  const [authState, setAuthState] = useState<AuthState>(() => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (token) {
        const decoded = parseJwt(token);
        if (decoded) {
          return {
            user: { id: decoded.sub, email: decoded.email, token },
            loading: false,
            error: null,
            isAuthenticated: true,
          };
        }
      }
    } catch (e) {
      // ignore and fall through to default
    }
    return { user: null, loading: false, error: null, isAuthenticated: false };
  });
  const router = useRouter();

  // Initial auth state is derived synchronously from localStorage via the useState initializer above.

  const signIn = async (email: string, password: string): Promise<string | null> => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      const token = await authHook.signIn(email, password);
      // If backend returned a token, store it and navigate. Otherwise return null.
      if (token) {
        localStorage.setItem('access_token', token);
        const decoded = parseJwt(token);
        if (decoded) {
          const user: User = { id: decoded.sub, email: decoded.email, token };
          setAuthState({ user, loading: false, error: null, isAuthenticated: true });
          // Navigate to dashboard after token is stored.
          window.location.href = '/tasks';
          return token;
        }
        // token present but couldn't decode — still return token
        localStorage.setItem('access_token', token);
        setAuthState({ user: null, loading: false, error: null, isAuthenticated: false });
        return token;
      }
      // No token
      setAuthState(prev => ({ ...prev, loading: false }));
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: msg || 'Sign in failed',
        isAuthenticated: false,
        user: null
      }));
      return null;
    }
  };

  const signUp = async (email: string, password: string): Promise<string | null> => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      const token = await authHook.signUp(email, password);
      if (token) {
        localStorage.setItem('access_token', token);
        const decoded = parseJwt(token);
        if (decoded) {
          const user: User = { id: decoded.sub, email: decoded.email, token };
          setAuthState({ user, loading: false, error: null, isAuthenticated: true });
          window.location.href = '/tasks';
          return token;
        }
        localStorage.setItem('access_token', token);
        setAuthState({ user: null, loading: false, error: null, isAuthenticated: false });
        return token;
      }
      setAuthState(prev => ({ ...prev, loading: false }));
      return null;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setAuthState(prev => ({
        ...prev,
        loading: false,
        error: msg || 'Sign up failed',
        isAuthenticated: false,
        user: null
      }));
      return null;
    }
  };

  const signOut = async () => {
    try {
      await authHook.signOut();
      setAuthState({
        user: null,
        loading: false,
        error: null,
        isAuthenticated: false
      });
      router.push('/signin');
    } catch (error) {
      console.error('Sign out error:', error);
      // Even if sign out fails, clear local state
      setAuthState({
        user: null,
        loading: false,
        error: null,
        isAuthenticated: false
      });
      router.push('/signin');
    }
  };

  const refreshAuth = async () => {
    // In a real implementation, you might want to validate the token
    // This function is maintained for compatibility
  };

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        signIn,
        signUp,
        signOut,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthContextProvider');
  }
  return context;
}

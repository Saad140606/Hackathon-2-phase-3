import { useRouter } from 'next/navigation';
import { useCallback } from 'react';
import apiClient from '@/lib/api/client';

// For now, since BetterAuth uses atoms instead of standard hooks, we'll create a simple wrapper
// that works with our existing system but represents the BetterAuth integration
interface User {
  id: string;
  email: string;
  token?: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshAuth: () => void;
}

export function useBetterAuth(): AuthContextType {
  const router = useRouter();

  // Direct API calls to match our backend endpoints
  const signInHandler = useCallback(async (email: string, password: string) => {
    try {
      // Attempt real sign-in and return the token (or null on failure).
      const response = await apiClient.post('/auth/signin', { email, password });
      const token = response?.data?.access_token || null;
      return token;
    } catch (err: unknown) {
      return null;
    }
  }, [router]);

  const signUpHandler = useCallback(async (email: string, password: string) => {
    try {
      const response = await apiClient.post('/auth/signup', { email, password });
      const token = response?.data?.access_token || null;
      return token;
    } catch (err: unknown) {
      return null;
    }
  }, [router]);

  const signOutHandler = useCallback(async () => {
    try {
      // Call backend to clear the httpOnly cookie
      await apiClient.post('/auth/signout', {});

      // Clear the stored token from localStorage
      localStorage.removeItem('access_token');

      // Redirect to sign in page
      router.push('/signin');
    } catch (error) {
      console.error('Sign out error:', error);
      // Even if sign out fails, clear local storage and redirect
      localStorage.removeItem('access_token');
      router.push('/signin');
    }
  }, [router]);

  const refreshAuth = useCallback(() => {
    // Session refreshing would happen automatically with JWT
  }, []);

  // Return initial state - the actual state will be managed by AuthContext
  return {
    user: null,
    loading: false,
    error: null,
    isAuthenticated: false,
    signIn: signInHandler,
    signUp: signUpHandler,
    signOut: signOutHandler,
    refreshAuth,
  };
}
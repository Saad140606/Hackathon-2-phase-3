/**
 * AuthGuard Component
 *
 * Wraps protected components and ensures user is authenticated.
 * Redirects to login if not authenticated, shows loading state while checking.
 */

"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api/client';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const router = useRouter();
  const [isAuth, setIsAuth] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return Boolean(localStorage.getItem('access_token'));
  });

  const [isChecking, setIsChecking] = useState<boolean>(() => !isAuth);

  useEffect(() => {
    if (isAuth) {
      // no-op: already authenticated via local token
      setIsChecking(false);
      return;
    }

    const checkAuth = async () => {
      try {
        const response = await apiClient.get('/auth/me');
        if (response.status === 200) {
          setIsAuth(true);
        } else {
          console.warn('Auth check non-200:', response.status, response.data);
          router.push('/signin');
        }
      } catch (err) {
        try {
          if (typeof err === 'object' && err !== null) console.error('Auth check failed (axios):', JSON.stringify(err));
          else console.error('Auth check failed (axios):', String(err));
        } catch {
          console.error('Auth check failed (axios):', err);
        }
        router.push('/signin');
      } finally {
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [isAuth, router]);

  // Show loading state while checking
  if (isChecking) {
    return (
      fallback || (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-gray-600">Checking authentication...</p>
          </div>
        </div>
      )
    );
  }

  // Don't render children if not authenticated (will redirect)
  if (!isAuth) {
    return null;
  }

  // Render children if authenticated
  return <>{children}</>;
}

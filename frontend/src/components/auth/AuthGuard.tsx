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
  const [isChecking, setIsChecking] = useState(true);
  const [isAuth, setIsAuth] = useState(false);

  useEffect(() => {
    // Fast path: if an access token exists in localStorage, consider user authenticated (dev fallback)
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      setIsAuth(true);
      setIsChecking(false);
      return;
    }

    // Check authentication status by calling backend via axios (sends credentials)
    const checkAuth = async () => {
      try {
        const response = await apiClient.get('/auth/me');
        if (response.status === 200) {
          setIsAuth(true);
          setIsChecking(false);
        } else {
          console.warn('Auth check non-200:', response.status, response.data);
          setIsAuth(false);
          setIsChecking(false);
          router.push('/signin');
        }
      } catch (error: any) {
        // Log detailed error to help debugging CORS/network issues
        console.error('Auth check failed (axios):', error?.response ?? error?.message ?? error);
        setIsAuth(false);
        setIsChecking(false);
        router.push('/signin');
      }
    };

    checkAuth();
  }, [router]);

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

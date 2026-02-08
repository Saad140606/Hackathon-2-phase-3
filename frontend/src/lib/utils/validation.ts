// Minimal validation utilities used by forms.

export function validateEmail(email: string): boolean {
  if (!email) return false;
  // simple RFC 5322-ish regex for basic validation
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email.toLowerCase());
}

export function validatePassword(password: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!password || password.length < 8) {
    errors.push('Password must be at least 8 characters');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain an uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain a lowercase letter');
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain a number');
  }
  if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]+/.test(password)) {
    errors.push('Password must contain a special character');
  }

  return { valid: errors.length === 0, errors };
}

export function validateTaskTitle(title: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!title || !title.trim()) {
    errors.push('Title is required');
  }
  const trimmed = title ? title.trim() : '';
  if (trimmed.length > 255) {
    errors.push('Title must be 255 characters or fewer');
  }
  return { valid: errors.length === 0, errors };
}

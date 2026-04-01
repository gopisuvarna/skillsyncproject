export interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export async function getCsrfToken(): Promise<string> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/me/`, {
    credentials: 'include',
  });
  return (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
}

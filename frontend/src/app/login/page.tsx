'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ShieldAlert, Mail, Lock, Loader2, ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please enter email and password");
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("username", email); // OAuth2 password spec
      formData.append("password", password);

      const res = await api.login(formData);
      toast.success(`Welcome back, ${res.name}!`);
      
      // Redirect based on role
      const role = res.role.toLowerCase();
      router.push(`/${role}/dashboard`);
    } catch (err: any) {
      toast.error(err.message || "Invalid credentials. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-950 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center space-x-2.5 mb-6">
          <div className="bg-blue-600 text-white p-2 rounded-xl shadow">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <span className="font-bold text-2xl text-slate-900 dark:text-white">CivicAI</span>
        </Link>
        <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Access Portal
        </h2>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Or{' '}
          <Link href="/register" className="font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-500 transition-colors">
            create a citizen account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-4 border border-slate-200 dark:border-slate-800 shadow-lg sm:rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-slate-700 dark:text-slate-200">
                Government ID / Email Address
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4.5 w-4.5" />
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@civicai.gov.in"
                  className="pl-10 w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-slate-700 dark:text-slate-200">
                Security Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4.5 w-4.5" />
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs font-semibold">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  defaultChecked
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 dark:border-slate-800 rounded cursor-pointer"
                />
                <label htmlFor="remember-me" className="ml-2 block text-slate-700 dark:text-slate-300 cursor-pointer">
                  Remember my session
                </label>
              </div>

              <div className="text-blue-600 dark:text-blue-400 hover:text-blue-500 cursor-pointer">
                Forgot password?
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition cursor-pointer"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <span className="flex items-center space-x-1">
                  <span>Sign In</span>
                  <ArrowRight className="h-4 w-4" />
                </span>
              )}
            </button>
          </form>

          {/* Seed credentials notice */}
          <div className="mt-8 border-t border-slate-200 dark:border-slate-800 pt-6">
            <h4 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">Seeded Demo Credentials:</h4>
            <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <p><span className="font-semibold text-slate-700 dark:text-slate-200">Citizen:</span> <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">citizen@gmail.com</code> / <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">citizenpassword</code></p>
              <p><span className="font-semibold text-slate-700 dark:text-slate-200">Officer (BBMP):</span> <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">officer.bbmp@civicai.gov.in</code> / <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">officerpassword</code></p>
              <p><span className="font-semibold text-slate-700 dark:text-slate-200">Administrator:</span> <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">admin@civicai.gov.in</code> / <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">adminpassword</code></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

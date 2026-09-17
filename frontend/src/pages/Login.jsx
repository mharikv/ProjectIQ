import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Factory, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-700 via-primary-800 to-primary-900 p-12 flex-col justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-white/10 p-3 rounded-xl">
            <Factory className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">ProjectIQ</h1>
            <p className="text-primary-200">AI Project Management Agent</p>
          </div>
        </div>
        <div>
          <h2 className="text-4xl font-bold text-white mb-4">Smart Project Management for Manufacturing</h2>
          <p className="text-primary-200 text-lg mb-8">AI-powered tools for charter generation, WBS, scheduling, resource optimization, risk management, and more.</p>
          <div className="grid grid-cols-2 gap-4">
            {['Project Charter', 'WBS Generator', 'Gantt Scheduling', 'Risk Management', 'Quality Control', 'Predictive Maintenance'].map((feature) => (
              <div key={feature} className="bg-white/10 rounded-lg px-4 py-3 text-white text-sm">{feature}</div>
            ))}
          </div>
        </div>
        <p className="text-primary-300 text-sm">&copy; 2026 ProjectIQ</p>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="bg-primary-600 p-2 rounded-lg">
              <Factory className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl font-bold">ProjectIQ</h1>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome back</h2>
          <p className="text-gray-500 mb-8">Sign in to manage your manufacturing projects</p>

          {error && (
            <div className="bg-danger-50 border border-danger-500/20 text-danger-600 px-4 py-3 rounded-lg mb-6 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="input-field" placeholder="Enter username" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} className="input-field pr-10" placeholder="Enter password" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full py-3">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

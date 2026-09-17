import { Outlet, Link, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Factory, LogOut, LayoutDashboard, PlayCircle, CheckCircle2 } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const view = searchParams.get('view') || 'in_progress';
  const isDashboard = location.pathname === '/';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinkClass = (active) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      active
        ? 'bg-primary-50 text-primary-700'
        : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/?view=in_progress" className="flex items-center gap-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <Factory className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">ProjectIQ</h1>
                <p className="text-xs text-gray-500">AI Project Management Agent</p>
              </div>
            </Link>
            <nav className="flex items-center gap-2 sm:gap-4">
              <Link to="/?view=in_progress" className={navLinkClass(isDashboard && view === 'in_progress')}>
                <PlayCircle className="w-4 h-4" />
                <span className="hidden sm:inline">In Progress</span>
              </Link>
              <Link to="/?view=completed" className={navLinkClass(isDashboard && view === 'completed')}>
                <CheckCircle2 className="w-4 h-4" />
                <span className="hidden sm:inline">Completed</span>
              </Link>
              <Link to="/?view=in_progress" className={`${navLinkClass(false)} hidden md:flex`}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              <div className="flex items-center gap-3 pl-2 sm:pl-4 border-l border-gray-200">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-900">{user?.full_name || user?.username}</p>
                  <p className="text-xs text-gray-500 capitalize">{user?.role?.replace('_', ' ')}</p>
                </div>
                <button onClick={handleLogout} className="p-2 text-gray-400 hover:text-danger-500 transition-colors" title="Logout">
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

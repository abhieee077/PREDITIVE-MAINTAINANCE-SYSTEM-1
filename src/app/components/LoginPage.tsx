import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, ArrowRight, Lock, User } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // No auth - just navigate to dashboard
    navigate('/overview');
  };

  return (
    <div className="min-h-screen bg-[#232f3e] flex items-center justify-center">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Activity className="w-10 h-10 text-[#ec7211]" />
            <span className="text-2xl font-semibold text-white">
              Industrial Maintenance
            </span>
          </div>
          <p className="text-[#879596] text-sm">
            Predictive Maintenance Console
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h2 className="text-xl font-semibold text-[#16191f] mb-6">
            Sign in to your account
          </h2>

          <form onSubmit={handleLogin}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-[#16191f] mb-2">
                Username or Operator ID
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#545b64]" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  className="w-full pl-10 pr-4 py-3 border border-[#d5dbdb] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ec7211] focus:border-transparent"
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-[#16191f] mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#545b64]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full pl-10 pr-4 py-3 border border-[#d5dbdb] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#ec7211] focus:border-transparent"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#ec7211] hover:bg-[#eb5f07] text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              Sign In
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-[#545b64]">
              Demo Mode - Click Sign In to continue
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-[#879596] text-sm">
          <p>Powered by NASA C-MAPSS Dataset</p>
          <p className="mt-1">XGBoost ML Predictions • Real-time Monitoring</p>
        </div>
      </div>
    </div>
  );
}

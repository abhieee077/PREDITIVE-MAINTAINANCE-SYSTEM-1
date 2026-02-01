import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    Activity,
    BarChart3,
    AlertTriangle,
    Settings,
    Users,
    Database,
    Bell,
    Search,
    Factory,
    Gauge,
    FileText
} from 'lucide-react';

interface LayoutProps {
    children: React.ReactNode;
}

const navItems = [
    { path: '/overview', label: 'Dashboard', icon: BarChart3 },
    { path: '/machines', label: 'Machines', icon: Factory },
    { path: '/alerts', label: 'Alerts', icon: AlertTriangle },
    { path: '/notifications', label: 'Notifications', icon: Bell },
    { path: '/analytics', label: 'Analytics', icon: Gauge },
    { path: '/logs', label: 'Maintenance Logs', icon: FileText },
];

export function Layout({ children }: LayoutProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const [notifications, setNotifications] = useState(0);

    useEffect(() => {
        const fetchNotificationCount = async () => {
            try {
                const res = await fetch('http://localhost:5000/api/alerts');
                const data = await res.json();
                const activeCount = (data.alerts || []).filter((a: any) => a.state === 'ACTIVE').length;
                setNotifications(activeCount);
            } catch (e) {
                console.error('Error fetching notifications:', e);
            }
        };
        fetchNotificationCount();
        const interval = setInterval(fetchNotificationCount, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="aws-layout">
            {/* Top Navigation Bar */}
            <header className="aws-topbar">
                <div className="aws-topbar-logo">
                    <Activity className="w-6 h-6" style={{ color: '#ec7211' }} />
                    <span>Industrial Maintenance Console</span>
                </div>

                <div className="aws-topbar-search">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/60" />
                        <input
                            type="text"
                            placeholder="Search machines, alerts..."
                            className="pl-9 w-full"
                        />
                    </div>
                </div>

                <div className="aws-topbar-actions">
                    <button className="aws-topbar-btn relative" onClick={() => navigate('/notifications')}>
                        <Bell className="w-5 h-5" />
                        {notifications > 0 && (
                            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center">
                                {notifications}
                            </span>
                        )}
                    </button>
                    <button className="aws-topbar-btn">
                        <Settings className="w-5 h-5" />
                    </button>
                    <button className="aws-topbar-btn">
                        <Users className="w-5 h-5" />
                        <span>Operator</span>
                    </button>
                </div>
            </header>

            {/* Sidebar */}
            <aside className="aws-sidebar">
                <nav className="aws-sidebar-nav">
                    <div className="aws-sidebar-section">Main Menu</div>

                    {navItems.map((item) => (
                        <div
                            key={item.path}
                            className={`aws-sidebar-item ${location.pathname === item.path ? 'active' : ''}`}
                            onClick={() => navigate(item.path)}
                        >
                            <item.icon className="w-5 h-5" />
                            <span>{item.label}</span>
                        </div>
                    ))}

                    <div className="aws-sidebar-divider" />

                    <div className="aws-sidebar-section">System</div>

                    <div className="aws-sidebar-item" onClick={() => navigate('/settings')}>
                        <Settings className="w-5 h-5" />
                        <span>Settings</span>
                    </div>
                    <div className="aws-sidebar-item">
                        <Database className="w-5 h-5" />
                        <span>Data Sources</span>
                    </div>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="aws-main">
                {children}
            </main>
        </div>
    );
}

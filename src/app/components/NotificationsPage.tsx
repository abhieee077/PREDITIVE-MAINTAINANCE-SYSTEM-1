import { useState, useEffect } from 'react';
import {
    Bell,
    BellRing,
    Check,
    X,
    AlertTriangle,
    XCircle,
    Info,
    Trash2,
    CheckCheck,
    RefreshCw
} from 'lucide-react';

interface Notification {
    id: string;
    type: 'critical' | 'warning' | 'info' | 'success';
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
    machine_id?: string;
}

export function NotificationsPage() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');

    useEffect(() => {
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/alerts');
            const data = await res.json();

            const notifs: Notification[] = (data.alerts || []).map((a: any) => ({
                id: a.id,
                type: a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warning' : 'info',
                title: `${a.severity.toUpperCase()} Alert - ${a.machine_id}`,
                message: a.message,
                timestamp: a.created_at,
                read: a.state !== 'ACTIVE',
                machine_id: a.machine_id
            }));

            setNotifications(notifs);
        } catch (error) {
            console.error('Error fetching notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id: string) => {
        try {
            await fetch(`http://localhost:5000/api/alerts/${id}/acknowledge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ operator_id: 'System' })
            });
            fetchNotifications();
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const markAllAsRead = async () => {
        const unreadNotifs = notifications.filter(n => !n.read);
        for (const notif of unreadNotifs) {
            await markAsRead(notif.id);
        }
    };

    const dismissNotification = async (id: string) => {
        try {
            await fetch(`http://localhost:5000/api/alerts/${id}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    operator_id: 'System',
                    root_cause: 'Notification dismissed',
                    resolution_notes: 'Dismissed by user',
                    downtime_minutes: 0
                })
            });
            fetchNotifications();
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const clearAllRead = async () => {
        const readNotifs = notifications.filter(n => n.read);
        for (const notif of readNotifs) {
            await dismissNotification(notif.id);
        }
    };

    const filteredNotifications = notifications.filter(n => {
        if (filter === 'unread') return !n.read;
        if (filter === 'read') return n.read;
        return true;
    });

    const getIcon = (type: string) => {
        switch (type) {
            case 'critical': return <XCircle className="w-5 h-5 text-red-500" />;
            case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
            case 'success': return <Check className="w-5 h-5 text-green-500" />;
            default: return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const getBg = (type: string, read: boolean) => {
        if (read) return 'bg-[#fafafa]';
        switch (type) {
            case 'critical': return 'bg-red-50 border-l-4 border-l-red-500';
            case 'warning': return 'bg-yellow-50 border-l-4 border-l-yellow-500';
            case 'success': return 'bg-green-50 border-l-4 border-l-green-500';
            default: return 'bg-blue-50 border-l-4 border-l-blue-500';
        }
    };

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    };

    const unreadCount = notifications.filter(n => !n.read).length;

    return (
        <div>
            {/* Page Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-semibold text-[#16191f] flex items-center gap-2">
                        <Bell className="w-6 h-6" />
                        Notifications
                        {unreadCount > 0 && (
                            <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-sm rounded-full">
                                {unreadCount} unread
                            </span>
                        )}
                    </h1>
                    <p className="text-sm text-[#545b64] mt-1">
                        System alerts and notifications
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={markAllAsRead}
                        disabled={unreadCount === 0}
                        className="aws-btn aws-btn-secondary flex items-center gap-2 disabled:opacity-50"
                    >
                        <CheckCheck className="w-4 h-4" />
                        Mark All Read
                    </button>
                    <button
                        onClick={clearAllRead}
                        className="aws-btn aws-btn-secondary flex items-center gap-2"
                    >
                        <Trash2 className="w-4 h-4" />
                        Clear Read
                    </button>
                    <button
                        onClick={fetchNotifications}
                        className="aws-btn aws-btn-secondary flex items-center gap-2"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 mb-4">
                {(['all', 'unread', 'read'] as const).map((status) => (
                    <button
                        key={status}
                        onClick={() => setFilter(status)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filter === status
                            ? 'bg-[#ec7211] text-white'
                            : 'bg-[#f2f3f3] text-[#545b64] hover:bg-[#eaeded]'
                            }`}
                    >
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                        <span className="ml-2 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                            {status === 'all' ? notifications.length :
                                status === 'unread' ? unreadCount :
                                    notifications.length - unreadCount}
                        </span>
                    </button>
                ))}
            </div>

            {/* Notifications List */}
            <div className="space-y-3">
                {loading ? (
                    <div className="aws-card p-8 text-center">
                        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#545b64]" />
                        Loading notifications...
                    </div>
                ) : filteredNotifications.length === 0 ? (
                    <div className="aws-card p-8 text-center">
                        <BellRing className="w-12 h-12 mx-auto mb-3 text-[#545b64] opacity-50" />
                        <p className="text-lg font-medium text-[#16191f]">No notifications</p>
                        <p className="text-sm text-[#545b64] mt-1">You're all caught up!</p>
                    </div>
                ) : (
                    filteredNotifications.map((notif) => (
                        <div
                            key={notif.id}
                            className={`aws-card p-4 ${getBg(notif.type, notif.read)} transition hover:shadow-md`}
                        >
                            <div className="flex items-start gap-4">
                                <div className="flex-shrink-0 mt-1">
                                    {getIcon(notif.type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className={`font-medium ${notif.read ? 'text-[#545b64]' : 'text-[#16191f]'}`}>
                                            {notif.title}
                                        </h3>
                                        {!notif.read && (
                                            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                                        )}
                                    </div>
                                    <p className="text-sm text-[#545b64] mt-1">{notif.message}</p>
                                    <p className="text-xs text-[#545b64] mt-2">{formatTime(notif.timestamp)}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    {!notif.read && (
                                        <button
                                            onClick={() => markAsRead(notif.id)}
                                            className="p-2 hover:bg-white rounded-lg transition"
                                            title="Mark as read"
                                        >
                                            <Check className="w-4 h-4 text-green-600" />
                                        </button>
                                    )}
                                    <button
                                        onClick={() => dismissNotification(notif.id)}
                                        className="p-2 hover:bg-white rounded-lg transition"
                                        title="Dismiss"
                                    >
                                        <X className="w-4 h-4 text-[#545b64]" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, Cell, ComposedChart
} from 'recharts';
import {
  Baby,
  Activity,
  ClipboardList,
  Play,
  Milk,
  Waves,
  Clock,
  TrendingUp,
  AlertCircle,
  MoreVertical,
  Camera,
  History,
  Bell,
  CheckCircle2,
  Calendar,
  Moon,
  Thermometer,
  Droplets,
  BarChart3,
  CalendarRange
} from 'lucide-react';

// --- Icons & Helpers ---
const PoopIcon = ({ size = 20, className = "" }) => (
  <span className={className} style={{ fontSize: size }}>💩</span>
);

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return 'No data';
  const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m ago`;
};

// --- Mock Data ---
// Replaced with API fetch
const INITIAL_LOGS = [];

const ANALYTICS_DATA = [
  { day: 'Mon', feeds: 6, diapers: 8, cries: 4, temp: 21 },
  { day: 'Tue', feeds: 7, diapers: 7, cries: 2, temp: 22 },
  { day: 'Wed', feeds: 5, diapers: 9, cries: 5, temp: 22.5 },
  { day: 'Thu', feeds: 8, diapers: 6, cries: 1, temp: 21.8 },
  { day: 'Fri', feeds: 6, diapers: 8, cries: 3, temp: 22.2 },
  { day: 'Sat', feeds: 7, diapers: 10, cries: 6, temp: 23 },
  { day: 'Sun', feeds: 6, diapers: 7, cries: 2, temp: 21.5 },
];

// --- Shared UI Components ---

const Card = ({ title, children, className = "", subtitle = "", icon: Icon }) => (
  <div className={`bg-white rounded-3xl p-6 shadow-sm border border-slate-100 ${className}`}>
    <div className="flex justify-between items-start mb-4">
      <div className="flex items-center space-x-2">
        {Icon && <Icon size={18} className="text-indigo-500" />}
        <div>
          {title && <h3 className="text-sm font-bold text-slate-800 uppercase tracking-tight">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>
      </div>
    </div>
    {children}
  </div>
);

const StatCard = ({ label, value, timeAgo, icon: Icon, colorClass }) => (
  <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center space-x-4">
    <div className={`p-3 rounded-xl ${colorClass}`}>
      <Icon size={20} />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider truncate">{label}</p>
      <p className="text-sm font-bold text-slate-800 truncate">{value}</p>
      {timeAgo && <p className="text-[10px] text-slate-400">{timeAgo}</p>}
    </div>
  </div>
);

// --- View 1: Monitor Home ---

const MonitorView = ({ logs }) => {
  const [isCrying, setIsCrying] = useState(false);

  useEffect(() => {
    // Check if the latest log is a recent cry event or if we should fetch from history
    // For now keeping simpler simulation or you could fetch /api/history
    const timer = setTimeout(() => setIsCrying(false), 2500);
    return () => clearTimeout(timer);
  }, []);

  const lastEvents = useMemo(() => {
    const getLatest = (type) => logs.find(l => l.type === type);
    return {
      feeding: getLatest('feeding'),
      pee: getLatest('pee'),
      poop: getLatest('poop'),
      sleep: getLatest('sleep')
    };
  }, [logs]);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Alert Banner */}
      {isCrying && (
        <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl flex items-center justify-between animate-pulse shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="bg-rose-500 p-2 rounded-full text-white">
              <AlertCircle size={20} />
            </div>
            <div>
              <p className="text-rose-900 font-bold text-sm">Crying Detected</p>
              <p className="text-rose-600 text-xs">Acoustic sensor triggered in the nursery.</p>
            </div>
          </div>
          <button
            onClick={() => setIsCrying(false)}
            className="text-xs font-bold text-rose-700 hover:underline px-4 py-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Hero Stats: Environmental Monitoring */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col items-center justify-center text-center space-y-1">
          <Thermometer className="text-orange-500 mb-1" size={24} />
          <span className="text-2xl font-black text-slate-800">22.4°C</span>
          <span className="text-[10px] font-bold text-slate-400 uppercase">Temp</span>
        </div>
        <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex flex-col items-center justify-center text-center space-y-1">
          <Droplets className="text-blue-500 mb-1" size={24} />
          <span className="text-2xl font-black text-slate-800">54%</span>
          <span className="text-[10px] font-bold text-slate-400 uppercase">Humidity</span>
        </div>
        <div className="col-span-2 hidden md:flex items-center px-6 bg-indigo-50 border border-indigo-100 rounded-3xl">
          <div className="space-y-1">
            <p className="text-xs font-bold text-indigo-900">Atmosphere is Optimal</p>
            <p className="text-[10px] text-indigo-600">The current conditions are perfect for a deep nap.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card title="Nursery Live Feed" className="overflow-hidden p-0 relative h-full">
            <div className="aspect-video lg:aspect-auto lg:h-[450px] bg-slate-900 flex items-center justify-center relative">
              <img
                src="/video_feed"
                alt="Live Nursery Feed"
                className="w-full h-full object-contain opacity-80"
              />
              <div className="absolute inset-0 bg-indigo-900/10 mix-blend-overlay"></div>

              <div className="absolute top-4 left-4 flex items-center space-x-2">
                <div className="bg-rose-600 text-white text-[10px] font-bold px-2 py-0.5 rounded flex items-center animate-pulse">
                  <div className="w-1.5 h-1.5 bg-white rounded-full mr-1.5"></div>
                  LIVE
                </div>
              </div>

              <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end">
                <div className="bg-black/40 backdrop-blur-md p-4 rounded-2xl text-white space-y-2">
                  <div className="flex items-center space-x-2">
                    <Activity size={14} className="text-emerald-400" />
                    <span className="text-xs font-bold tracking-tight">Movement: Still</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Bell size={14} className="text-sky-400" />
                    <span className="text-xs font-bold tracking-tight">Sound: Quiet</span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button className="p-3 bg-white/20 backdrop-blur-md rounded-full text-white hover:bg-white/40 transition-all">
                    <Camera size={20} />
                  </button>
                  <button className="p-3 bg-indigo-600 rounded-full text-white hover:bg-indigo-700 transition-all shadow-lg">
                    <Play size={20} fill="white" />
                  </button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest px-1">Status Summary</h4>

          <StatCard
            label="Last Feeding"
            value={lastEvents.feeding?.details || "None logged"}
            timeAgo={formatTimeAgo(lastEvents.feeding?.timestamp)}
            icon={Milk}
            colorClass="bg-blue-50 text-blue-600"
          />

          <StatCard
            label="Last Diaper"
            value={`${lastEvents.pee ? 'Pee' : ''}${lastEvents.poop ? ' & Poop' : ''}`}
            timeAgo={formatTimeAgo(lastEvents.pee?.timestamp || lastEvents.poop?.timestamp)}
            icon={Waves}
            colorClass="bg-emerald-50 text-emerald-600"
          />

          <StatCard
            label="Last Poop"
            value={lastEvents.poop?.intensity || "None today"}
            timeAgo={formatTimeAgo(lastEvents.poop?.timestamp)}
            icon={PoopIcon}
            colorClass="bg-amber-50 text-amber-600"
          />

          <StatCard
            label="Current State"
            value="Napping"
            timeAgo={formatTimeAgo(lastEvents.sleep?.timestamp)}
            icon={Moon}
            colorClass="bg-indigo-50 text-indigo-600"
          />

          <div className="p-6 bg-slate-900 rounded-3xl text-white shadow-xl shadow-slate-200">
            <p className="text-[10px] font-bold uppercase text-slate-400 mb-2">Proactive Insight</p>
            <p className="text-sm font-medium leading-relaxed">
              Based on environmental trends, the room might warm up by <span className="text-orange-400">0.5°C</span> in the next hour.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- View 2: Logging ---

const LoggingView = ({ logs, onAddLog }) => {
  const [selectedType, setSelectedType] = useState(null);
  const [notes, setNotes] = useState('');
  const [time, setTime] = useState(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false }));
  const [intensity, setIntensity] = useState('Medium');
  const [milkAmount, setMilkAmount] = useState('');
  const [feedingTime, setFeedingTime] = useState('');
  const [status, setStatus] = useState('');

  const handleLog = async () => {
    if (!selectedType) return;
    setStatus('Logging...');

    // Convert time input to ISO string
    const now = new Date();
    const [hours, minutes] = time.split(':');
    const timestampDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), parseInt(hours), parseInt(minutes));

    try {
      const payload = {
        event_type: selectedType,
        notes: notes || `${selectedType} event`,
        timestamp: timestampDate.toISOString(),
        intensity: intensity
      };

      // Add optional fields for feeding
      if (selectedType === 'feeding') {
        if (milkAmount) payload.milk_quantity_ml = parseInt(milkAmount);
        if (feedingTime) payload.feeding_time_min = parseInt(feedingTime);
      }

      const response = await fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const newLog = {
          id: Date.now(),
          type: selectedType,
          details: notes || `${selectedType} event`,
          timestamp: timestampDate.toISOString(),
          intensity: intensity,
          milk_quantity_ml: payload.milk_quantity_ml,
          feeding_time_min: payload.feeding_time_min
        };
        onAddLog(newLog);
        setStatus('Saved!');
        setNotes('');
        setMilkAmount('');
        setFeedingTime('');
        setTimeout(() => setStatus(''), 2000);
      } else {
        setStatus('Error saving');
      }
    } catch (e) {
      console.error(e);
      setStatus('Error saving');
    }
  };

  const eventTypes = [
    { id: 'feeding', icon: Milk, label: 'Feeding', color: 'bg-blue-100 text-blue-600' },
    { id: 'pee', icon: Waves, label: 'Pee', color: 'bg-emerald-100 text-emerald-600' },
    { id: 'poop', icon: PoopIcon, label: 'Poop', color: 'bg-amber-100 text-amber-600', isEmoji: true },
    { id: 'sleep', icon: Moon, label: 'Sleep', color: 'bg-indigo-100 text-indigo-600' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {eventTypes.map(type => (
          <button
            key={type.id}
            onClick={() => setSelectedType(type.id)}
            className={`flex flex-col items-center justify-center p-6 rounded-3xl border-2 transition-all ${selectedType === type.id ? 'border-indigo-600 bg-indigo-50 shadow-inner scale-95' : 'border-transparent bg-white shadow-sm hover:shadow-md'
              }`}
          >
            <div className={`p-4 rounded-2xl mb-3 flex items-center justify-center ${type.color}`}>
              <type.icon size={28} />
            </div>
            <span className="font-bold text-slate-700">{type.label}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Event Details" className="md:col-span-2">
          {selectedType ? (
            <div className="space-y-4">
              {/* Conditional Inputs for Feeding */}
              {selectedType === 'feeding' && (
                <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-2xl border border-blue-100">
                  <div>
                    <label className="block text-xs font-bold text-blue-700 mb-2 uppercase tracking-widest">Amount (ml)</label>
                    <input
                      type="number"
                      className="w-full bg-white border-blue-200 border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. 150"
                      value={milkAmount}
                      onChange={e => setMilkAmount(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-blue-700 mb-2 uppercase tracking-widest">Duration (min)</label>
                    <input
                      type="number"
                      className="w-full bg-white border-blue-200 border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. 15"
                      value={feedingTime}
                      onChange={e => setFeedingTime(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Notes</label>
                <textarea
                  className="w-full bg-slate-50 border-none rounded-2xl p-4 focus:ring-2 focus:ring-indigo-500 h-32"
                  placeholder={`e.g., Left side, consistency...`}
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Time</label>
                  <div className="relative">
                    <Clock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input
                      type="time"
                      className="w-full bg-slate-50 border-none rounded-xl pl-12 pr-4 py-3"
                      value={time}
                      onChange={e => setTime(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Intensity</label>
                  <select
                    className="w-full bg-slate-50 border-none rounded-xl px-4 py-3 appearance-none"
                    value={intensity}
                    onChange={e => setIntensity(e.target.value)}
                  >
                    <option>Small</option>
                    <option>Medium</option>
                    <option>Large</option>
                  </select>
                </div>
              </div>
              <button
                onClick={handleLog}
                className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 flex items-center justify-center space-x-2"
                disabled={status === 'Logging...'}
              >
                {status === 'Saved!' ? <CheckCircle2 size={20} /> : null}
                <span>{status || 'Save Event'}</span>
              </button>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400">
              <ClipboardList className="mb-2 opacity-20" size={48} />
              <p className="text-sm font-medium tracking-tight">Select a category above</p>
            </div>
          )}
        </Card>

        <Card title="Recent Logs" icon={History}>
          <div className="space-y-4">
            {logs.slice(0, 5).map((item, idx) => (
              <div key={idx} className="flex items-center space-x-3 group">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs 
                  ${item.type === 'feeding' ? 'bg-blue-50 text-blue-500' :
                    item.type === 'pee' ? 'bg-emerald-50 text-emerald-500' :
                      item.type === 'poop' ? 'bg-amber-50 text-amber-500' : 'bg-slate-50'}`}>
                  {item.type === 'feeding' ? <Milk size={14} /> :
                    item.type === 'pee' ? <Waves size={14} /> :
                      item.type === 'poop' ? <PoopIcon size={14} /> :
                        <Moon size={14} />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-slate-700 capitalize truncate">{item.type}</p>
                  <p className="text-[10px] text-slate-400 truncate">{item.details}</p>
                </div>
                <span className="text-[10px] font-bold text-slate-300">{formatTimeAgo(item.timestamp)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

// --- View 3: Analytics Dashboard ---

const AnalyticsView = ({ data, feedingData, stats }) => {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Feeding Analysis */}
        <Card title="Detailed Feeding Analysis" subtitle="Volume (ml) vs Duration (min) per feed" icon={Milk} className="lg:col-span-2">
          <div className="h-80 w-full mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={feedingData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="timeDisplay" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <YAxis yAxisId="left" orientation="left" stroke="#6366f1" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6366f1' }} label={{ value: 'ml', angle: -90, position: 'insideLeft', fill: '#6366f1' }} />
                <YAxis yAxisId="right" orientation="right" stroke="#f97316" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#f97316' }} label={{ value: 'min', angle: 90, position: 'insideRight', fill: '#f97316' }} />
                <Tooltip
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '12px', fontWeight: 'bold' }} />
                <Bar yAxisId="left" dataKey="amount" fill="#6366f1" radius={[4, 4, 0, 0]} name="Volume (ml)" barSize={20} />
                <Line yAxisId="right" type="monotone" dataKey="duration" stroke="#f97316" strokeWidth={3} dot={{ r: 4, fill: '#f97316', strokeWidth: 2, stroke: '#fff' }} name="Duration (min)" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Weekly Event Frequency */}
        <Card title="Weekly Activity Frequency" subtitle="Distribution of events over the last 7 days" icon={BarChart3}>
          <div className="h-80 w-full mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <Tooltip
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px', fontSize: '12px', fontWeight: 'bold' }} />
                <Bar dataKey="feeds" fill="#6366f1" radius={[4, 4, 0, 0]} name="Feeds" />
                <Bar dataKey="diapers" fill="#10b981" radius={[4, 4, 0, 0]} name="Diapers" />
                <Bar dataKey="cries" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Cry Episodes" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Temperature Trend */}
        <Card title="Nursery Temperature Trend" subtitle="Average daily temperature (°C)" icon={Thermometer}>
          <div className="h-80 w-full mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <YAxis domain={[18, 25]} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#f97316"
                  strokeWidth={4}
                  dot={{ r: 4, fill: '#f97316', strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 6 }}
                  name="Avg Temp"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Aggregate Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Feeds" value={stats.totalFeeds} timeAgo="This week" icon={Milk} colorClass="bg-indigo-50 text-indigo-600" />
        <StatCard label="Total Diapers" value={stats.totalDiapers} timeAgo="This week" icon={Waves} colorClass="bg-emerald-50 text-emerald-600" />
        <StatCard label="Cry Count" value={stats.totalCries} timeAgo="This week" icon={TrendingUp} colorClass="bg-rose-50 text-rose-600" />
        <StatCard label="Avg Temp" value={`${stats.avgTemp}°C`} timeAgo="7 day avg" icon={Thermometer} colorClass="bg-orange-50 text-orange-600" />
      </div>
    </div>
  );
};

// --- Main App Entry ---

export default function App() {
  const [activeTab, setActiveTab] = useState('monitor');
  const [logs, setLogs] = useState(INITIAL_LOGS);
  const [history, setHistory] = useState([]);

  // Fetch initial logs and history
  useEffect(() => {
    Promise.all([
      fetch('/api/logs').then(res => res.json()),
      fetch('/api/history').then(res => res.json())
    ]).then(([logsData, historyData]) => {
      if (Array.isArray(logsData)) setLogs(logsData);
      if (Array.isArray(historyData)) setHistory(historyData);
    }).catch(err => console.error("Failed to fetch data:", err));
  }, []);

  // Process data for analytics
  const { analyticsData, feedingData, stats } = useMemo(() => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const now = new Date();
    // Initialize last 7 days buckets
    const dailyBuckets = Array(7).fill(0).map((_, i) => {
      const d = new Date(now);
      d.setDate(d.getDate() - (6 - i));
      return {
        date: d.toDateString(),
        day: days[d.getDay()],
        feeds: 0,
        diapers: 0,
        cries: 0,
        temp: 21 + Math.random() * 2 // Mock temp for now as we don't log it
      };
    });

    const bucketMap = {};
    dailyBuckets.forEach((b, i) => bucketMap[b.date] = i);

    let totalFeeds = 0;
    let totalDiapers = 0;

    // Process Logs
    logs.forEach(log => {
      const date = new Date(log.timestamp).toDateString();
      // Since logs can be older than 7 days, we only count if in mapped buckets
      // Or if we want strictly last 7 days display?
      // Let's match strictly by date string
      const bucketIndex = bucketMap[date];
      if (bucketIndex !== undefined) {
        if (log.type === 'feeding') {
          dailyBuckets[bucketIndex].feeds++;
          totalFeeds++;
        } else if (log.type === 'pee' || log.type === 'poop') {
          dailyBuckets[bucketIndex].diapers++;
          totalDiapers++;
        }
      }
    });

    let totalCries = 0;
    // Process History (Cries)
    history.forEach(item => {
      // history item: { timestamp: 123456789 (epoch seconds), probability: 0.9, is_cry: true, ... }
      // Wait, did I fix the history endpoint?
      // server.py: get_history returns { timestamp: row[0], ... }
      // And row[0] comes from db.get_recent_predictions_bigquery which returns row.event_timestamp.timestamp() (seconds)
      // Correct.
      if (item.is_cry) {
        const date = new Date(item.timestamp * 1000).toDateString();
        const bucketIndex = bucketMap[date];
        if (bucketIndex !== undefined) {
          dailyBuckets[bucketIndex].cries++;
          totalCries++;
        }
      }
    });

    const avgTemp = (dailyBuckets.reduce((acc, curr) => acc + curr.temp, 0) / 7).toFixed(1);

    const feedingData = logs
      .filter(l => l.type === 'feeding')
      .map(l => ({
        timestamp: l.timestamp,
        timeDisplay: new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        amount: l.milk_quantity_ml || 0,
        duration: l.feeding_time_min || 0
      }))
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    return {
      analyticsData: dailyBuckets,
      feedingData,
      stats: { totalFeeds, totalDiapers, totalCries, avgTemp }
    };

  }, [logs, history]);

  const addLog = (newLog) => {
    setLogs(prev => [newLog, ...prev]);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'monitor': return <MonitorView logs={logs} />;
      case 'logging': return <LoggingView logs={logs} onAddLog={addLog} />;
      case 'analytics': return <AnalyticsView data={analyticsData} feedingData={feedingData} stats={stats} />;
      default: return <MonitorView logs={logs} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-24 lg:pb-8">
      {/* Desktop Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-slate-100 hidden lg:flex flex-col p-6 z-20 shadow-sm">
        <div className="flex items-center space-x-3 mb-10 px-2">
          <div className="bg-indigo-600 p-2 rounded-2xl shadow-lg shadow-indigo-100">
            <Baby className="text-white" size={24} />
          </div>
          <h1 className="text-xl font-black text-slate-800 tracking-tight">LittleWatch</h1>
        </div>

        <nav className="flex-1 space-y-2">
          {[
            { id: 'monitor', label: 'Monitor', icon: Activity },
            { id: 'logging', label: 'Log Event', icon: ClipboardList },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-2xl transition-all duration-200 ${activeTab === item.id ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200' : 'text-slate-500 hover:bg-slate-50'
                }`}
            >
              <item.icon size={20} />
              <span className="font-bold text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="mt-auto p-4 bg-slate-50 rounded-3xl flex items-center space-x-3 border border-slate-100">
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" className="w-10 h-10 rounded-full bg-white p-0.5 border" alt="User" />
          <div className="overflow-hidden">
            <p className="text-xs font-black text-slate-800 truncate">Guardian</p>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Felix's Mom</p>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <main className="lg:pl-64 min-h-screen">
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-slate-100 px-6 py-4 flex items-center justify-between">
          <div className="lg:hidden">
            <div className="bg-indigo-600 p-1.5 rounded-xl">
              <Baby className="text-white" size={22} />
            </div>
          </div>

          <div>
            <h2 className="text-lg font-black text-slate-800 flex items-center space-x-2">
              <span>{activeTab === 'monitor' ? 'Nursery Home' : activeTab === 'logging' ? 'Quick Logger' : 'Insights & Trends'}</span>
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-slate-100 rounded-full text-slate-500 border border-slate-200">
              <CalendarRange size={14} />
              <span className="text-[10px] font-black uppercase tracking-widest">{new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            </div>
            <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors">
              <Bell size={20} />
            </button>
          </div>
        </header>

        <div className="p-6 md:p-8">
          {renderContent()}
        </div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-100 px-8 py-3 lg:hidden flex justify-around items-center shadow-[0_-8px_30px_rgb(0,0,0,0.04)] z-50 rounded-t-[32px]">
        {[
          { id: 'monitor', icon: Activity, label: 'Home' },
          { id: 'logging', icon: ClipboardList, label: 'Log' },
          { id: 'analytics', icon: BarChart3, label: 'Trends' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center space-y-1 transition-all ${activeTab === tab.id ? 'text-indigo-600 scale-110' : 'text-slate-300'
              }`}
          >
            <div className={`p-2.5 rounded-2xl ${activeTab === tab.id ? 'bg-indigo-50' : ''}`}>
              <tab.icon size={22} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-tighter">{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
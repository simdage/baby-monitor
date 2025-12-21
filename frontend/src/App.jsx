import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, AreaChart, Area, Cell
} from 'recharts';
import {
  Baby,
  Activity,
  Tag,
  ClipboardList,
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Milk,
  Waves,
  Clock,
  TrendingUp,
  AlertCircle,
  MoreVertical,
  ChevronRight,
  Camera,
  Layers,
  History
} from 'lucide-react';

// Custom Poop Icon since it's missing from the standard lucide set
const PoopIcon = ({ size = 20, className = "" }) => (
  <span className={className} style={{ fontSize: size }}>💩</span>
);

// --- Mock Data ---

const CRYING_DATA = [
  { time: '00:00', intensity: 20, predicted: 15 },
  { time: '04:00', intensity: 80, predicted: 75 },
  { time: '08:00', intensity: 30, predicted: 40 },
  { time: '12:00', intensity: 10, predicted: 5 },
  { time: '16:00', intensity: 45, predicted: 50 },
  { time: '20:00', intensity: 90, predicted: 85 },
  { time: '23:59', intensity: 40, predicted: 35 },
];

const LABELING_SAMPLES = [
  { id: 1, timestamp: '2023-10-27 02:15:00', audioUrl: '#', imageUrl: 'https://images.unsplash.com/photo-1519689680058-324335c77eba?auto=format&fit=crop&q=80&w=400', initialLabel: 'Hungry', confidence: 0.92 },
  { id: 2, timestamp: '2023-10-27 04:30:00', audioUrl: '#', imageUrl: 'https://images.unsplash.com/photo-1555252333-9f8e92e65df9?auto=format&fit=crop&q=80&w=400', initialLabel: 'Discomfort', confidence: 0.78 },
  { id: 3, timestamp: '2023-10-27 06:00:00', audioUrl: '#', imageUrl: 'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&q=80&w=400', initialLabel: 'Tired', confidence: 0.85 },
];

const LOG_HISTORY = [
  { id: 1, type: 'feeding', details: '150ml Formula', time: '10:30 AM', timestamp: 10.5 },
  { id: 2, type: 'diaper_pee', details: 'Pee', time: '11:15 AM', timestamp: 11.25 },
  { id: 3, type: 'diaper_poop', details: 'Poop', time: '01:20 PM', timestamp: 13.33 },
  { id: 4, type: 'feeding', details: 'Breast milk', time: '04:45 PM', timestamp: 16.75 },
  { id: 5, type: 'diaper_pee', details: 'Pee', time: '07:10 PM', timestamp: 19.16 },
];

// --- Shared Components ---

const SidebarItem = ({ icon: Icon, label, active, onClick, customIcon }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${active ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-slate-100'
      }`}
  >
    {customIcon ? customIcon : <Icon size={20} />}
    <span className="font-medium">{label}</span>
  </button>
);

const Card = ({ title, children, className = "", subtitle = "" }) => (
  <div className={`bg-white rounded-3xl p-6 shadow-sm border border-slate-100 ${className}`}>
    <div className="flex justify-between items-start mb-4">
      <div>
        {title && <h3 className="text-lg font-semibold text-slate-800">{title}</h3>}
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
    </div>
    {children}
  </div>
);

// --- Main Views ---

const AnalyticsView = () => {
  const [cryingData, setCryingData] = useState([]);

  useEffect(() => {
    fetch('/api/history')
      .then(res => res.json())
      .then(data => {
        // Transform backend data to chart format
        // Backend returns: { timestamp, probability, is_cry, gcs_uri } (descending)
        if (data && data.length > 0) {
          const formatted = data.reverse().map(d => {
            const date = new Date(d.timestamp * 1000);
            return {
              time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              // Use probability * 100 for prediction
              predicted: Math.round(d.probability * 100),
              // Visualization: If it was classified as cry, show high intensity, else low
              intensity: d.is_cry ? Math.max(Math.round(d.probability * 100), 60) : Math.round(d.probability * 20)
            };
          });
          setCryingData(formatted);
        }
      })
      .catch(err => console.error("Failed to fetch history:", err));
  }, []);

  // Process LOG_HISTORY for charting
  const eventCounts = useMemo(() => {
    const counts = { feeding: 0, pee: 0, poop: 0 };
    LOG_HISTORY.forEach(item => {
      if (item.type === 'feeding') counts.feeding++;
      if (item.type === 'diaper_pee') counts.pee++;
      if (item.type === 'diaper_poop') counts.poop++;
    });
    return [
      { name: 'Feeding', value: counts.feeding, color: '#6366f1' },
      { name: 'Pee', value: counts.pee, color: '#10b981' },
      { name: 'Poop', value: counts.poop, color: '#f59e0b' },
    ];
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Crying Chart */}
        <Card className="lg:col-span-2" title="Crying Intensity vs. Predictions" subtitle="Real-time analysis from BigQuery data">
          <div className="h-80 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cryingData}>
                <defs>
                  <linearGradient id="colorInt" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Area type="monotone" dataKey="intensity" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorInt)" name="Actual Crying" />
                <Area type="monotone" dataKey="predicted" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" fill="transparent" name="AI Prediction" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <div className="space-y-6">
          <Card title="Quick Insights" className="bg-indigo-50 border-none">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Avg Duration</span>
                <span className="font-bold text-indigo-700 font-mono">14.2 min</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Peak Time</span>
                <span className="font-bold text-indigo-700 font-mono">08:00 PM</span>
              </div>
              <div className="pt-2 border-t border-indigo-100">
                <div className="flex items-center text-xs text-indigo-500 space-x-1">
                  <TrendingUp size={12} />
                  <span>+5% from yesterday</span>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Alert History">
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex items-start space-x-3 p-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                  <div className="p-2 bg-rose-100 text-rose-600 rounded-full">
                    <AlertCircle size={14} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">Heavy Crying Detected</p>
                    <p className="text-xs text-slate-400">2h ago • Nursery Cam</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* NEW: Log Observation View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Daily Event Distribution" subtitle="Aggregate count of logged events">
          <div className="h-64 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={eventCounts} layout="vertical" margin={{ left: 10, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} width={80} />
                <Tooltip
                  cursor={{ fill: 'transparent' }}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={32}>
                  {eventCounts.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Unified Activity Timeline" subtitle="Correlation of physical needs and behavior">
          <div className="mt-4 relative pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
            {LOG_HISTORY.map((event, idx) => (
              <div key={event.id} className="relative">
                <div className={`absolute -left-8 top-1.5 w-6 h-6 rounded-full border-4 border-white shadow-sm flex items-center justify-center
                  ${event.type === 'feeding' ? 'bg-blue-500' : event.type.includes('poop') ? 'bg-amber-500' : 'bg-emerald-500'}`}
                >
                  {event.type === 'feeding' ? <Milk size={10} className="text-white" /> :
                    event.type.includes('poop') ? <span className="text-[10px]">💩</span> :
                      <Waves size={10} className="text-white" />}
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold text-slate-700 capitalize">{event.type.replace('_', ' ')}</p>
                    <p className="text-xs text-slate-400">{event.details}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-bold text-slate-500">{event.time}</p>
                    {/* Visual context of crying intensity at that time */}
                    <div className="mt-1 flex space-x-1 justify-end">
                      {[1, 2, 3, 4, 5].map(tick => (
                        <div key={tick} className={`h-1 w-2 rounded-full ${tick <= (idx + 1) % 5 + 1 ? 'bg-indigo-300' : 'bg-slate-100'}`} />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div className="pt-2 text-center">
              <button className="text-xs font-bold text-indigo-600 hover:text-indigo-700 transition-colors">
                View Detailed Correlation Map
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

const LabelingView = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const sample = LABELING_SAMPLES[currentIndex];

  const handleLabel = (label) => {
    console.log(`Labeled sample ${sample.id} as ${label}`);
    if (currentIndex < LABELING_SAMPLES.length - 1) {
      setCurrentIndex(prev => prev + 1);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card>
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-slate-800">Review Crying Prediction</h3>
          <span className="px-3 py-1 bg-slate-100 rounded-full text-xs font-medium text-slate-500">
            Sample {currentIndex + 1} of {LABELING_SAMPLES.length}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <div className="relative aspect-video rounded-2xl overflow-hidden bg-slate-100 group">
              <img src={sample.imageUrl} alt="Baby snapshot" className="w-full h-full object-cover" />
              <div className="absolute top-4 left-4 bg-black/50 backdrop-blur-md px-3 py-1 rounded-full text-white text-xs flex items-center space-x-2">
                <Camera size={12} />
                <span>Nursery South Cam</span>
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-slate-600">Audio Recording</span>
                <span className="text-xs text-slate-400">0:15 / 0:30</span>
              </div>
              <div className="flex items-center space-x-4">
                <button className="p-3 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 shadow-md">
                  <Play size={20} fill="white" />
                </button>
                <div className="flex-1 h-1 bg-slate-200 rounded-full relative overflow-hidden">
                  <div className="absolute left-0 top-0 bottom-0 w-1/2 bg-indigo-500 rounded-full" />
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">AI Prediction</label>
              <div className="mt-2 flex items-center justify-between p-4 bg-indigo-50 rounded-2xl border border-indigo-100">
                <span className="text-indigo-900 font-bold text-lg">{sample.initialLabel}</span>
                <span className="text-indigo-600 font-mono font-medium">{(sample.confidence * 100).toFixed(0)}% Match</span>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Correct Label</label>
              <div className="grid grid-cols-2 gap-3">
                {['Hungry', 'Tired', 'Diaper', 'Bored', 'Sick', 'Discomfort'].map(label => (
                  <button
                    key={label}
                    onClick={() => handleLabel(label)}
                    className="py-3 px-4 border border-slate-200 rounded-xl text-slate-700 hover:border-indigo-600 hover:bg-indigo-50 transition-all font-medium text-sm"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-4 flex space-x-3">
              <button className="flex-1 py-4 bg-slate-800 text-white rounded-2xl font-bold hover:bg-slate-900 transition-all">
                Confirm AI Label
              </button>
              <button
                onClick={() => handleLabel('Skip')}
                className="px-6 py-4 bg-slate-100 text-slate-500 rounded-2xl font-bold hover:bg-slate-200 transition-all"
              >
                Skip
              </button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

const LoggingView = () => {
  const [selectedType, setSelectedType] = useState(null);

  const eventTypes = [
    { id: 'feeding', icon: Milk, label: 'Feeding', color: 'bg-blue-100 text-blue-600' },
    { id: 'pee', icon: Waves, label: 'Pee', color: 'bg-emerald-100 text-emerald-600' },
    { id: 'poop', icon: PoopIcon, label: 'Poop', color: 'bg-amber-100 text-amber-600', isEmoji: true },
    { id: 'other', icon: ClipboardList, label: 'Other', color: 'bg-slate-100 text-slate-600' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {eventTypes.map(type => (
          <button
            key={type.id}
            onClick={() => setSelectedType(type.id)}
            className={`flex flex-col items-center justify-center p-6 rounded-3xl border-2 transition-all ${selectedType === type.id ? 'border-indigo-600 bg-indigo-50' : 'border-transparent bg-white shadow-sm hover:shadow-md'
              }`}
          >
            <div className={`p-4 rounded-2xl mb-3 flex items-center justify-center ${type.color}`}>
              {type.isEmoji ? <type.icon size={28} /> : <type.icon size={28} />}
            </div>
            <span className="font-bold text-slate-700">{type.label}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Quick Log Form" className="md:col-span-2">
          {selectedType ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-500 mb-2">Notes</label>
                <textarea
                  className="w-full bg-slate-50 border-none rounded-2xl p-4 focus:ring-2 focus:ring-indigo-500 h-32"
                  placeholder={`Describe the ${selectedType} event...`}
                />
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-500 mb-2">Time</label>
                  <div className="relative">
                    <Clock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input type="time" className="w-full bg-slate-50 border-none rounded-xl pl-12 pr-4 py-3" defaultValue="14:16" />
                  </div>
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-500 mb-2">Intensity/Amount</label>
                  <select className="w-full bg-slate-50 border-none rounded-xl px-4 py-3">
                    <option>Small</option>
                    <option>Medium</option>
                    <option>Large</option>
                  </select>
                </div>
              </div>
              <button className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100">
                Log Event
              </button>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-400">
              <Activity className="mb-2 opacity-20" size={48} />
              <p>Select an event type above to start logging</p>
            </div>
          )}
        </Card>

        <Card title="Recent History">
          <div className="space-y-4">
            {LOG_HISTORY.map(item => (
              <div key={item.id} className="flex items-center space-x-3 group cursor-pointer">
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                  {item.type === 'feeding' ? <Milk size={18} /> :
                    item.type === 'diaper_pee' ? <Waves size={18} /> :
                      item.type === 'diaper_poop' ? <PoopIcon size={18} /> :
                        <ClipboardList size={18} />}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-700 capitalize">{item.type.replace('_', ' ')}</p>
                  <p className="text-xs text-slate-400">{item.details}</p>
                </div>
                <span className="text-[10px] font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded uppercase">{item.time}</span>
              </div>
            ))}
            <button className="w-full text-center text-xs font-bold text-indigo-600 mt-4 hover:underline">
              View All History
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState('analytics');

  const renderContent = () => {
    switch (activeTab) {
      case 'analytics': return <AnalyticsView />;
      case 'labeling': return <LabelingView />;
      case 'logging': return <LoggingView />;
      default: return <AnalyticsView />;
    }
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case 'analytics': return 'Observation Dashboard';
      case 'labeling': return 'Classifier Training';
      case 'logging': return 'Daily Baby Logs';
      default: return 'Baby Monitor';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-indigo-100 selection:text-indigo-700">
      {/* Sidebar - Desktop */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-slate-100 hidden lg:flex flex-col p-6">
        <div className="flex items-center space-x-3 mb-10 px-2">
          <div className="bg-gradient-to-tr from-indigo-600 to-violet-500 p-2 rounded-2xl shadow-lg shadow-indigo-100">
            <Baby className="text-white" size={24} />
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600">
            LittleWatch
          </h1>
        </div>

        <nav className="flex-1 space-y-2">
          <SidebarItem
            icon={Activity}
            label="Observation"
            active={activeTab === 'analytics'}
            onClick={() => setActiveTab('analytics')}
          />
          <SidebarItem
            icon={Tag}
            label="Relabel Data"
            active={activeTab === 'labeling'}
            onClick={() => setActiveTab('labeling')}
          />
          <SidebarItem
            icon={ClipboardList}
            label="Log Events"
            active={activeTab === 'logging'}
            onClick={() => setActiveTab('logging')}
          />
        </nav>

        <div className="mt-auto p-4 bg-slate-50 rounded-2xl">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-indigo-200 border-2 border-white shadow-sm overflow-hidden ring-1 ring-white">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-800">Momma Doe</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Primary Guardian</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:pl-64 min-h-screen transition-all duration-300">
        <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-slate-100 px-4 md:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4 lg:hidden">
            <div className="bg-indigo-600 p-2 rounded-xl">
              <Baby className="text-white" size={20} />
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-slate-800">{getPageTitle()}</h2>
            <p className="text-xs text-slate-400 hidden md:block">Real-time data from Cloud Storage & BigQuery</p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex -space-x-2 mr-4">
              {[1, 2].map(i => (
                <div key={i} className="w-8 h-8 rounded-full border-2 border-white bg-slate-200 overflow-hidden ring-1 ring-slate-100">
                  <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${i * 12}`} alt="User" />
                </div>
              ))}
              <div className="w-8 h-8 rounded-full border-2 border-white bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-500 ring-1 ring-slate-100">
                +2
              </div>
            </div>
            <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors">
              <MoreVertical size={20} />
            </button>
          </div>
        </header>

        <div className="p-4 md:p-8 pb-24 lg:pb-8">
          {renderContent()}
        </div>

        {/* Mobile Nav */}
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-100 px-6 py-3 lg:hidden flex justify-between items-center shadow-2xl z-50">
          {[
            { id: 'analytics', icon: Activity },
            { id: 'labeling', icon: Tag },
            { id: 'logging', icon: ClipboardList }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`p-3 rounded-2xl transition-all ${activeTab === tab.id ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400'
                }`}
            >
              <tab.icon size={24} />
            </button>
          ))}
        </nav>
      </main>
    </div>
  );
}
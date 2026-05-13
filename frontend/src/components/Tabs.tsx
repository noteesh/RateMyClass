/**
 * Tabs — simple two-tab switcher used to toggle between Leaderboard and Dashboard.
 * Keeps no internal state; the active tab is controlled by the parent.
 */

interface Tab {
  id: string;
  label: string;
  badge?: number;   // optional count shown next to label
}

interface Props {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
}

export default function Tabs({ tabs, active, onChange }: Props) {
  return (
    <div className="flex gap-1 rounded-xl bg-slate-100 p-1 w-fit">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold transition-all
            ${active === tab.id
              ? "bg-white text-indigo-700 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
            }`}
        >
          {tab.label}
          {tab.badge !== undefined && (
            <span className={`rounded-full px-2 py-0.5 text-xs font-bold
              ${active === tab.id ? "bg-indigo-100 text-indigo-600" : "bg-slate-200 text-slate-500"}`}>
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

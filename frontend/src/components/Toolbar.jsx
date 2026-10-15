import { CATEGORIES, STATUS_LABEL } from '../constants.js';

const TABS = [
  { value: '', label: 'All' },
  { value: 'LOST', label: 'Lost' },
  { value: 'FOUND', label: 'Found' },
];

export default function Toolbar({ filters, onChange }) {
  const set = (key) => (e) => onChange({ ...filters, [key]: e.target ? e.target.value : e });

  return (
    <section className="toolbar">
      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.label}
            role="tab"
            aria-selected={filters.type === tab.value}
            className={filters.type === tab.value ? 'tab active' : 'tab'}
            onClick={() => set('type')(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="filters">
        <input
          type="search"
          placeholder="Search title, description or place…"
          value={filters.q}
          onChange={set('q')}
          aria-label="Search"
        />
        <select value={filters.category} onChange={set('category')} aria-label="Category">
          <option value="">All categories</option>
          {Object.entries(CATEGORIES).map(([value, { label, icon }]) => (
            <option key={value} value={value}>{icon} {label}</option>
          ))}
        </select>
        <select value={filters.status} onChange={set('status')} aria-label="Status">
          <option value="">Any status</option>
          {Object.entries(STATUS_LABEL).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>
    </section>
  );
}

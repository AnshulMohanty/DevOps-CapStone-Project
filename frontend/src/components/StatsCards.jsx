const CARDS = [
  { key: 'open_lost', label: 'Still lost', icon: '❓', tone: 'lost' },
  { key: 'open_found', label: 'Found, waiting for owner', icon: '🙋', tone: 'found' },
  { key: 'returned', label: 'Returned to owner', icon: '🤝', tone: 'returned' },
  { key: 'total', label: 'Reports in total', icon: '📋', tone: 'total' },
];

export default function StatsCards({ stats }) {
  return (
    <section className="stats" aria-label="Board summary">
      {CARDS.map(({ key, label, icon, tone }) => (
        <div className={`stat ${tone}`} key={key}>
          <span className="stat-icon" aria-hidden="true">{icon}</span>
          <div>
            <strong>{stats[key]}</strong>
            <small>{label}</small>
          </div>
        </div>
      ))}
    </section>
  );
}

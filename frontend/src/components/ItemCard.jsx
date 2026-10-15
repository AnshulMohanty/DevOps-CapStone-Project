import { CATEGORIES, STATUS_LABEL, timeAgo } from '../constants.js';

export default function ItemCard({ item, busy, onClaim, onResolve, onDelete }) {
  const category = CATEGORIES[item.category] ?? CATEGORIES.OTHER;
  const done = item.status === 'RETURNED';

  return (
    <article className={`card ${done ? 'done' : ''}`}>
      <div className="card-top">
        <span className={`badge type-${item.type.toLowerCase()}`}>{item.type}</span>
        <span className={`badge status-${item.status.toLowerCase()}`}>{STATUS_LABEL[item.status]}</span>
      </div>

      <h3>
        <span aria-hidden="true">{category.icon}</span> {item.title}
      </h3>
      {item.description && <p className="desc">{item.description}</p>}

      <dl className="meta">
        <div><dt>📍</dt><dd>{item.location}</dd></div>
        <div><dt>👤</dt><dd>{item.reported_by}{item.contact && ` · ${item.contact}`}</dd></div>
        <div><dt>🕒</dt><dd>{timeAgo(item.created_at)} · {category.label}</dd></div>
      </dl>

      <div className="actions">
        {item.status === 'OPEN' && (
          <button className="btn small" disabled={busy} onClick={onClaim}>Mark claimed</button>
        )}
        {!done && (
          <button className="btn small success" disabled={busy} onClick={onResolve}>Mark returned</button>
        )}
        {done && <span className="returned-note">✓ Returned {item.resolved_at && timeAgo(item.resolved_at)}</span>}
        <button className="btn small ghost danger" disabled={busy} onClick={onDelete} aria-label={`Delete ${item.title}`}>
          Delete
        </button>
      </div>
    </article>
  );
}

export const CATEGORIES = {
  ELECTRONICS: { label: 'Electronics', icon: '💻' },
  ID_CARD: { label: 'ID card', icon: '🪪' },
  BOOKS: { label: 'Books', icon: '📚' },
  BOTTLE: { label: 'Bottle', icon: '🧴' },
  CLOTHING: { label: 'Clothing', icon: '🧥' },
  OTHER: { label: 'Other', icon: '📦' },
};

export const STATUS_LABEL = { OPEN: 'Open', CLAIMED: 'Claimed', RETURNED: 'Returned' };

export function timeAgo(iso) {
  // SQLite drops the timezone; the API always stores UTC, so read a bare timestamp as UTC.
  const when = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  const minutes = Math.round((Date.now() - when.getTime()) / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return when.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
}

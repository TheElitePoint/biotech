"""Source adapters: one module per data origin, each emitting Tavily-shaped raw items.

`intent_pipeline.signals.normalize()` only needs a dict shaped like
{url, title, content, raw_content, published_date, _seed_id, _query,
_signal_type, _date_window_days} — it was never actually Tavily-specific, just
Tavily-shaped. Every adapter in this package targets that same shape so the
existing normalize -> resolve_company -> dedupe -> gates.route -> store
pipeline works unchanged regardless of which free API produced the item.
"""

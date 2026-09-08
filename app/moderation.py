HIDE_THRESHOLD = 3  # a piece of content collapses behind a click-to-reveal once it hits this many reports


def get_report_counts(client, target_type: str, target_ids: list) -> dict:
    """Returns {target_id: report_count} for the given ids. Never raises —
    moderation counts are a nice-to-have, not something that should break
    a page if the query fails."""
    if not target_ids:
        return {}
    try:
        rows = (
            client.table("reports")
            .select("target_id")
            .eq("target_type", target_type)
            .in_("target_id", target_ids)
            .execute()
            .data
        )
    except Exception:
        return {}
    counts = {}
    for r in rows:
        counts[r["target_id"]] = counts.get(r["target_id"], 0) + 1
    return counts

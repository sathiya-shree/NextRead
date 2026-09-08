BADGE_DEFS = [
    {"key": "first_page", "name": "First Page", "desc": "Marked your first book as read",
     "check": lambda s: s["books_read"] >= 1},
    {"key": "bookworm", "name": "Bookworm", "desc": "Read 10 books",
     "check": lambda s: s["books_read"] >= 10},
    {"key": "bibliophile", "name": "Bibliophile", "desc": "Read 25 books",
     "check": lambda s: s["books_read"] >= 25},
    {"key": "reviewer", "name": "Reviewer", "desc": "Wrote 5 reviews",
     "check": lambda s: s["reviews_count"] >= 5},
    {"key": "critic", "name": "Critic", "desc": "Wrote 20 reviews",
     "check": lambda s: s["reviews_count"] >= 20},
    {"key": "popular", "name": "Popular", "desc": "10 followers",
     "check": lambda s: s["followers_count"] >= 10},
    {"key": "streak_keeper", "name": "Streak Keeper", "desc": "7-day reading streak",
     "check": lambda s: s["streak"] >= 7},
    {"key": "marathon_reader", "name": "Marathon Reader", "desc": "30-day reading streak",
     "check": lambda s: s["streak"] >= 30},
    {"key": "club_regular", "name": "Club Regular", "desc": "Member of 3+ clubs",
     "check": lambda s: s["clubs_count"] >= 3},
]


def compute_badges(stats: dict) -> list:
    return [
        {"name": b["name"], "description": b["desc"], "unlocked": bool(b["check"](stats))}
        for b in BADGE_DEFS
    ]

"""The 35 cities the scraper covers, and the weekly rotation that decides which cities run on which day."""

CITIES_PER_DAY = 5

def cities_scraped_on(weekday):
    """Cities scraped on a weekday (0=Monday ... 6=Sunday). The 7 days cover all cities once per week."""
    return [CITIES[(weekday * CITIES_PER_DAY + i) % len(CITIES)] for i in range(CITIES_PER_DAY)]

CITIES = [
    # Week 1 (5 cities per day = 35 total cities)
    ("Nashville", "TN"),
    ("Dallas", "TX"),
    ("Charlotte", "NC"),
    ("Denver", "CO"),
    ("Phoenix", "AZ"),
    ("Houston", "TX"),
    ("San Antonio", "TX"),
    ("Austin", "TX"),
    ("Atlanta", "GA"),
    ("Miami", "FL"),
    ("Tampa", "FL"),
    ("Orlando", "FL"),
    ("Boston", "MA"),
    ("New York", "NY"),
    ("Philadelphia", "PA"),
    ("Washington", "DC"),
    ("Baltimore", "MD"),
    ("Chicago", "IL"),
    ("Detroit", "MI"),
    ("Minneapolis", "MN"),
    ("Kansas City", "MO"),
    ("St. Louis", "MO"),
    ("Memphis", "TN"),
    ("New Orleans", "LA"),
    ("Los Angeles", "CA"),
    ("San Diego", "CA"),
    ("San Francisco", "CA"),
    ("Seattle", "WA"),
    ("Portland", "OR"),
    ("Las Vegas", "NV"),
    ("Salt Lake City", "UT"),
    ("Indianapolis", "IN"),
    ("Columbus", "OH"),
    ("Cleveland", "OH"),
    ("Pittsburgh", "PA"),
]

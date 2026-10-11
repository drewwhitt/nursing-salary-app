"""
Shared database helpers.

Supabase returns at most 1000 rows per request by default, so a plain
`.select(...).execute()` silently truncates the jobs table once it grows past
that. fetch_all_rows() pages through the whole table instead.
"""

PAGE_SIZE = 1000


def fetch_all_rows(supabase, select='*', table='jobs'):
    """Return every row of `table` matching `select`, fetched page by page."""
    rows = []
    start = 0
    while True:
        # Order by the primary key so pages are stable between requests
        batch = (
            supabase.table(table)
            .select(select)
            .order('job_id')
            .range(start, start + PAGE_SIZE - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE

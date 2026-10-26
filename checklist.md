# Milestone 1 checklist audit

Audit scope: Bao only, based on the evidence available on 26 October 2026. The source checklist is a separate instruction document; this page records evidence/statuses without changing project crawl data or code.

**Rows:** 75 | **PASS:** 18 | **FAIL:** 4 | **NOT CHECKED:** 53 | **N/A:** 0

The complete requirement-by-requirement ledger is [checklist.csv](checklist.csv). Items without direct evidence remain `NOT CHECKED`. The major open blockers are the incomplete crawl, performance benchmark, public Pages verification, group-wide consistency, and final submission checks.

## Priority actions

1. Resolve or formally account for 48 unavailable source versions and 15 failed reference tasks.
2. Run the required CPU-only Colab benchmark, including sampled mean and peak memory over the process tree and peak disk usage.
3. Review all five members’ assigned ranges and shards for overlap, schema, and status consistency.
4. Publish and verify the Jupyter Book on GitHub Pages, then test links anonymously.
5. Record Moodle deadline, final commit/tag, and a clean-clone sample run.

# Geo-bucket property API

## Scope and assumptions

This MVP serves Lagos property searches. A neighbourhood is a human place name,
not an H3 cell. Labels are supplied by users and are not independently geocoded.
Prices are integers in kobo, with currency NGN and multiplier 100. No listing
authentication, updates, deletion, or external geocoding is included.

## Geographic grouping

Each coordinate maps deterministically to an H3 resolution-8 cell. Its average
hexagon area is approximately 0.737 km² and average edge length about 531 m;
individual cells vary. Store the true H3 centre and polygon as PostGIS geography
with SRID 4326. Geography area calculations return square metres. SQL points
use longitude first; H3's Python API accepts latitude first.

A cell is a fixed grid unit, not a radius-based cluster. No distance threshold
or insertion-order-dependent nearest-centre decision is needed. Close properties
can occupy different cells. Every observed label registers aliases in its own
cell, and search retrieves every matching cell without a five-cell cap.

We do not automatically include neighbouring cells: that would add locations
for which there is no matching alias. A neighbourhood can span multiple cells;
a cell can overlap several named areas. Returning all properties in a matched
cell deliberately approximates neighbourhood membership.

## Schema and indexes

![Database schema showing properties, geo buckets, and bucket aliases](db_schema.png)

```text
geo_buckets (UUID PK, unique H3 cell, centroid, boundary)
    | 1                         | 1
    |                           |
    v many                      v many
properties                  bucket_aliases
(UUID PK, bucket FK,         (bucket FK, normalized alias)
 title, raw name,            composite primary key
 coordinates, price,
 currency, rooms, timestamps)
```

- `geo_buckets.h3_index` has a unique B-tree index for deterministic upserts.
- GiST indexes on bucket centroid and boundary support spatial queries.
- `properties(bucket_id, created_at, id)` supports bucket-based lookup.
- Alias B-tree supports exact matching; `GIN(alias gin_trgm_ops)` supports typo
  candidate lookup using the `%` operator.
- Required fields, coordinate limits, nonnegative prices/room counts, and positive
  currency multipliers are validated in the API and/or database constraints.
- Property foreign keys restrict deleting occupied buckets; alias foreign keys
  cascade when a bucket is removed. Repeated aliases within a cell are unique.

Counts are computed directly. There are no denormalized counters to reconcile
on failed or concurrent writes. Exact global counts and area aggregates require
work proportional to the relevant rows and are not constant-time operations.

## Ingestion and transactions

`POST /api/properties` validates the request, computes H3 geometry, upserts the
bucket with `ON CONFLICT DO NOTHING`, finds its ID, upserts aliases, and inserts
the property. One transaction encloses all steps. The unique H3 constraint
serializes competing creation of the same cell; alias uniqueness handles repeat
labels. A failed property insert rolls back newly created buckets and aliases.
Repeated POSTs intentionally create distinct listings; no idempotency key exists.

Synchronous SQLAlchemy sessions run in synchronous FastAPI handlers. Each request
gets its own session; connections are pooled and returned when the session closes.

## Name matching

1. Unicode NFKC normalization, case folding, punctuation removal, and whitespace
   collapse produce a normalized full label.
2. Register the full label and a primary alias obtained by removing explicit
   trailing `Ajah` and `Lagos` qualifiers while preserving at least one word.
   This makes all three supplied Sangotedo labels register `sangotedo`.
   Multiword names such as `Victoria Island` remain intact.
3. Normalize search the same way. Match full/primary aliases exactly first.
4. If no exact match exists and the normalized query has at least three
   characters, use pg_trgm `%` with a transaction-local threshold of 0.3.
   This is a heuristic, not a guarantee of semantic equivalence.
5. Fetch properties through the matching bucket-ID subquery, using `IN` to avoid
   duplicates from multiple aliases. Return total count and a page ordered by
   creation time and UUID. Defaults: limit 50; maximum 100; offset starts at zero.

```text
User text -> normalization -> indexed exact alias lookup
                                      |
                               no match? trigram lookup
                                      |
                               matching bucket IDs
                                      |
                           properties.bucket_id lookup
                                      |
                          ordered, paginated properties
```

The text never needs to be compared against every property row. An exact match
takes precedence over fuzzy candidates to reduce unrelated results. The threshold
can still produce false positives and needs a larger labelled evaluation set.
Two geographically distant places with the same name can both match; a future
city/map-centre filter would disambiguate them. Broad searches for `Ajah` do not
promise every child neighbourhood without a geographic hierarchy.

## Stats and coverage

`GET /api/geo-buckets/stats` returns total buckets, total properties, paginated
per-bucket counts, and coverage. Coverage is the sum of the actual areas of
occupied H3 cells in km² plus the bounding box of property coordinates. It is
not building footprint area or the official area of a neighbourhood. Empty
results have zero area and null bounds. Aggregates are live, so concurrent writes
can make separate stats statements reflect slightly different instants.

## Verification

Tests mirror the source modules under `tests/unit` and `tests/integration`.
Unit tests mock database dependencies to verify HTTP validation and responses.
Integration tests start a disposable PostGIS container through Testcontainers,
run real migrations and `alembic check`, and clear application tables between
cases. Cases cover the three labels, case differences, typos, unrelated areas,
adjacent cells, pagination, counts, foreign keys, alias uniqueness, and rollback
after a real constraint violation. FastAPI's TestClient exercises the three
addresses with real sessions against the container's database. No separate HTTP
server is started. Containers are cleaned up afterward; the developer's
application database is never used.

`seed.py` includes three Sangotedo variants plus Ikeja and Victoria Island.
Its fixed property IDs make repeated execution safe. H3 cell IDs and polygons
are generated using the same helpers as ingestion.

## Scaling and alternatives

At 500,000 properties, keep text lookup on aliases and property retrieval on
bucket IDs. Measure representative queries with `EXPLAIN (ANALYZE, BUFFERS)`;
no latency claim follows from an index alone. Large matches, exact counts, deep
offsets, and sorting remain costs. Start with bounded responses and pooling;
then consider keyset pagination, cached stats, and cached alias-to-cell mappings.

Radius buckets with PostGIS `ST_DWithin` are a valid indexed alternative, but
text queries still need coordinates and bucket centres need a selection rule.
Administrative polygons give clearer membership when reliable boundaries exist;
informal neighbourhoods often lack them. H3 resolution 7 has larger cells and
mixes more neighbourhoods. Resolution 8 is a practical MVP compromise.

With more time: curated neighbourhood identities and aliases, explicit city
filters, property-level place membership, concurrency/load tests, and relevance
evaluation. Global geographic use would also require testing cell polygons that
cross the antimeridian and careful coverage-bound calculations there.

References: [H3 cell statistics](https://h3geo.org/docs/core-library/restable/),
[PostGIS ST_DWithin](https://postgis.net/docs/ST_DWithin.html).

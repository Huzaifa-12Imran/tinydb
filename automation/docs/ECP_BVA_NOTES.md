# ECP and BVA notes

Project under test: TinyDB (https://github.com/msiemens/tinydb, MIT license)
Modules under test: tinydb/utils.py, tinydb/queries.py, tinydb/middlewares.py

ECP = equivalence class partitioning. BVA = boundary value analysis.
Each class or boundary below names the automated test that covers it.

----------------------------------------------------------------------
## 1. tinydb/utils.py

### 1.1 LRUCache(capacity)

Input: capacity
- Valid class A: None (unlimited). Expect no eviction. Test: test_set_with_unlimited_capacity_never_evicts
- Valid class B: positive integer. Expect eviction after capacity is exceeded.
- Boundary classes: 0 and negative. Expect nothing is ever stored (length 0 after set).
- Boundary values for N in 1, 2, 3, 10: N items kept, N+1 items evicts exactly the oldest.
  Tests: test_set_exactly_capacity_items_keeps_all, test_set_capacity_plus_one_items_evicts_exactly_the_oldest, test_set_with_zero_or_negative_capacity_stores_nothing

set(key, value)
- Class: new key. Expect stored. Test: test_set_stores_value_for_new_key
- Class: existing key. Expect overwrite, same length, key becomes most recent. Tests: test_set_existing_key_overwrites_value_and_keeps_length, test_set_existing_key_moves_it_to_most_recent
- Class: new key on full cache. Expect oldest key evicted. Test: test_set_evicts_least_recently_used_key_first
- Class: existing key on full cache. Expect no eviction. Test: test_set_overwrite_on_full_cache_does_not_evict

get(key, default=None)
- Class: present key. Expect value and recency refresh. Tests: test_get_existing_key_returns_value, test_get_refreshes_recency_so_other_key_is_evicted
- Class: missing key. Expect default (None or given), order unchanged. Tests: test_get_missing_key_returns_none_by_default, test_get_missing_key_returns_given_default, test_get_missing_key_does_not_change_order
- Class: stored None. Expect None, not the default (sentinel logic). Test: test_get_stored_none_returns_none_not_default
- Class: stored falsy values 0, "", [], False. Expect returned as stored. Test: test_get_returns_falsy_stored_values

__getitem__ / __setitem__
- Class: present key. Expect value. Test: test_getitem_existing_key_returns_value
- Class: missing key. Expect KeyError carrying the key. Tests: test_getitem_missing_key_raises_keyerror, test_getitem_keyerror_carries_the_missing_key

__delitem__ / pop
- Class: present key. Expect removed, slot freed. Tests: test_delitem_removes_key, test_delitem_frees_a_slot_so_no_eviction_happens
- Class: missing key. Expect KeyError. Test: test_delitem_missing_key_raises_keyerror

clear(), lru, length, __contains__, __iter__
- clear on empty cache is a no-op (boundary). Test: test_clear_on_empty_cache_is_a_noop
- length boundaries 0, 1, 2. Test: test_length_matches_number_of_items
- lru is a copy, oldest first. Tests: test_lru_lists_oldest_key_first, test_lru_returns_a_copy_not_the_internal_state
- "in" must not refresh recency. Test: test_contains_does_not_refresh_recency

### 1.2 freeze(obj) and FrozenDict

Input classes for freeze: dict, list, tuple, set, scalar (int, float, str, None, bool).
- dict becomes FrozenDict. list becomes tuple. tuple gets nested elements frozen. set becomes frozenset. Scalars returned unchanged (same object).
- Nested mix (dict containing list containing dict) is frozen recursively and hashable.
- Boundary: empty dict, empty list, empty tuple, empty set.
- Original object must not be modified.

FrozenDict
- Equal content gives equal hash regardless of insertion order. Different content gives different hash.
- Negative class: every mutator (setitem, delitem, clear, setdefault, popitem, update, pop) raises TypeError and leaves content unchanged.
- Boundary: empty FrozenDict is hashable.

----------------------------------------------------------------------
## 2. tinydb/queries.py

### 2.1 Query path building
- Class: empty query evaluated directly. Expect RuntimeError.
- Class: operator used with no path. Expect ValueError.
- Class: attribute path and item path. Expect identical behaviour.
- Class: missing key at any depth, or non-mapping in the middle of the path. Expect False (no exception).

### 2.2 Comparison operators ==, !=, <, <=, >, >=
Classes per operator: value satisfies, value does not satisfy, field missing (always False, also for !=).
Boundary values around the threshold 18: 17 (below), 18 (on), 19 (above) for each of >=, <, <=, >.
Also: int vs float compare numerically. Incomparable types (str vs int) raise TypeError from the comparison itself.
Data driven coverage: data/query_cases.csv (18 rows).

### 2.3 exists
Classes: key present, key absent, key present with None value (True), nested path present and absent.
Boundary: empty document.

### 2.4 matches and search
Classes: matching string, non matching string, non string value (int, None, list, float) which gives False.
matches uses re.match, so it anchors at the start only (prefix match). search finds the pattern anywhere.
Observation: the docstring of matches says the whole string has to match, the code only checks the start. Worth mentioning in the report.
Regex flags: IGNORECASE changes the result and also changes query identity (cache key).
Boundary: empty string against .* (match) and .+ (no match).

### 2.5 test and map
Classes: function returns True, returns False, extra arguments forwarded, field missing (function must not be called).
map: applies the function to the path value and makes the query uncacheable.

### 2.6 any, all, one_of
any with list: overlap, no overlap. any with sub query: one element matches, none match. Boundary: empty list gives False. Negative: a string value is not treated as a sequence.
all with list: all present, one missing. all with sub query: all match, one fails. Boundary: empty list with sub query gives True (vacuous), empty required list gives True.
one_of: value in list, value not in list. Boundary: empty list never matches.

### 2.7 fragment and noop
fragment: all keys equal, value mismatch, key missing. Boundary: empty fragment matches every document.
noop: always True, neutral element for &.

### 2.8 Combinators & | ~
Full truth table for & and | (four input combinations each). ~ inverts, ~~ restores.

### 2.9 Hashing and cache identity
Same query gives equal hash and equality. Different value gives a different query. & and | are commutative for equality and hash. Plain comparison queries are cacheable, map() makes a query and any combination with it uncacheable.

----------------------------------------------------------------------
## 3. tinydb/middlewares.py

### 3.1 Middleware (base class)
- __call__ creates the storage, returns the middleware itself, forwards constructor arguments.
- __getattr__ forwards unknown attributes to the storage. Missing attribute raises AttributeError.
- Middlewares can be nested.

### 3.2 CachingMiddleware

WRITE_CACHE_SIZE (threshold) boundary analysis for sizes 1, 2, 3, 5:
- threshold minus 1 writes: storage not written (0 storage writes)
- exactly threshold writes: storage written once with the last data
- threshold plus 1 writes: still one storage write, a new batch starts with counter 1
Data driven coverage: data/cache_flush_cases.csv (8 rows: sizes 1, 2, 3, 5, 1000 with different write counts).

read
- Class: empty storage returns None. Test: test_first_read_of_empty_storage_returns_none
- Class: data present in cache, later storage changes are not seen. Test: test_read_serves_from_cache_after_the_first_read
- Boundary observation: an empty storage (None) is not cached, so it is read again every time. Test: test_empty_storage_is_not_cached_so_it_is_read_again
- Negative: read after close raises ValueError.

write
- Goes to cache only, storage untouched until the threshold. Negative: write after close raises ValueError.

flush
- Class: pending writes get written. Boundary: flush with 0 pending writes does nothing. Second flush without new writes does nothing. Counter resets to 0. Negative: flush after close raises ValueError.

close
- Flushes pending data, closes the underlying storage, clears the cache, is idempotent. Close without pending writes does not write.

Integration with TinyDB
- Documents readable through the cache. With JSONStorage the file stays empty until close. Data survives close and reopen.

----------------------------------------------------------------------
## Techniques summary

ECP: used for every function above to pick one representative per valid and invalid class.
BVA: used for LRUCache capacity (0, N, N+1), age threshold 18 in comparison operators, empty containers, WRITE_CACHE_SIZE threshold (size minus 1, size, size plus 1), empty documents and empty strings.
Negative testing: KeyError, TypeError, ValueError, RuntimeError, AttributeError paths.

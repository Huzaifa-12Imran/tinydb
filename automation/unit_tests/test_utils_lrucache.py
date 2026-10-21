"""
Module 1, class LRUCache (tinydb/utils.py)

Owner: Member 1 (replace with your name before committing)

Techniques: ECP, BVA. See docs/ECP_BVA_NOTES.md section 1.
Functions covered: set, get, __getitem__, __delitem__, clear, lru, length,
__contains__, __iter__ and the inherited MutableMapping helpers.
"""
import pytest

from tinydb.utils import LRUCache

pytestmark = pytest.mark.utils


def filled(capacity, keys):
    cache = LRUCache(capacity)
    for index, key in enumerate(keys):
        cache.set(key, index)
    return cache


class TestSet:
    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_set_stores_value_for_new_key(self):
        cache = LRUCache(3)
        cache.set("a", 1)
        assert cache["a"] == 1

    @pytest.mark.ecp
    def test_set_existing_key_overwrites_value_and_keeps_length(self):
        cache = filled(3, ["a", "b"])
        cache.set("a", 99)
        assert cache["a"] == 99
        assert len(cache) == 2

    @pytest.mark.ecp
    def test_set_existing_key_moves_it_to_most_recent(self):
        cache = filled(3, ["a", "b", "c"])
        cache.set("a", 0)
        assert cache.lru == ["b", "c", "a"]

    @pytest.mark.ecp
    def test_set_evicts_least_recently_used_key_first(self):
        cache = filled(2, ["a", "b", "c"])
        assert cache.lru == ["b", "c"]
        assert "a" not in cache

    @pytest.mark.ecp
    def test_set_with_unlimited_capacity_never_evicts(self):
        cache = LRUCache()
        for number in range(1000):
            cache.set(number, number)
        assert len(cache) == 1000

    @pytest.mark.ecp
    def test_set_overwrite_on_full_cache_does_not_evict(self):
        cache = filled(2, ["a", "b"])
        cache.set("b", 5)
        assert cache.lru == ["a", "b"]

    @pytest.mark.bva
    @pytest.mark.parametrize("capacity", [1, 2, 3, 10])
    def test_set_exactly_capacity_items_keeps_all(self, capacity):
        keys = [f"k{i}" for i in range(capacity)]
        cache = filled(capacity, keys)
        assert cache.lru == keys

    @pytest.mark.bva
    @pytest.mark.parametrize("capacity", [1, 2, 3, 10])
    def test_set_capacity_plus_one_items_evicts_exactly_the_oldest(self, capacity):
        keys = [f"k{i}" for i in range(capacity + 1)]
        cache = filled(capacity, keys)
        assert cache.lru == keys[1:]
        assert len(cache) == capacity

    @pytest.mark.bva
    @pytest.mark.parametrize("capacity", [0, -1])
    def test_set_with_zero_or_negative_capacity_stores_nothing(self, capacity):
        cache = LRUCache(capacity)
        cache.set("a", 1)
        assert len(cache) == 0
        assert "a" not in cache


class TestGet:
    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_get_existing_key_returns_value(self):
        assert filled(2, ["a"]).get("a") == 0

    @pytest.mark.ecp
    def test_get_missing_key_returns_none_by_default(self):
        assert LRUCache(2).get("missing") is None

    @pytest.mark.ecp
    def test_get_missing_key_returns_given_default(self):
        assert LRUCache(2).get("missing", "fallback") == "fallback"

    @pytest.mark.ecp
    def test_get_refreshes_recency_so_other_key_is_evicted(self):
        cache = filled(2, ["a", "b"])
        cache.get("a")
        cache.set("c", 2)
        assert cache.lru == ["a", "c"]

    @pytest.mark.ecp
    def test_get_missing_key_does_not_change_order(self):
        cache = filled(3, ["a", "b", "c"])
        cache.get("zzz")
        assert cache.lru == ["a", "b", "c"]

    @pytest.mark.ecp
    def test_get_stored_none_returns_none_not_default(self):
        cache = LRUCache(2)
        cache.set("a", None)
        assert cache.get("a", "fallback") is None

    @pytest.mark.ecp
    @pytest.mark.parametrize("falsy", [0, "", [], False])
    def test_get_returns_falsy_stored_values(self, falsy):
        cache = LRUCache(2)
        cache.set("a", falsy)
        assert cache.get("a", "fallback") == falsy


class TestGetItem:
    @pytest.mark.ecp
    def test_getitem_existing_key_returns_value(self):
        assert filled(2, ["a", "b"])["b"] == 1

    @pytest.mark.negative
    def test_getitem_missing_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            LRUCache(2)["missing"]

    @pytest.mark.negative
    def test_getitem_keyerror_carries_the_missing_key(self):
        with pytest.raises(KeyError) as error:
            LRUCache(2)["missing"]
        assert error.value.args == ("missing",)

    @pytest.mark.ecp
    def test_getitem_refreshes_recency(self):
        cache = filled(2, ["a", "b"])
        _ = cache["a"]
        cache["c"] = 2
        assert cache.lru == ["a", "c"]

    @pytest.mark.ecp
    def test_getitem_works_for_stored_none(self):
        cache = LRUCache(2)
        cache["a"] = None
        assert cache["a"] is None

    @pytest.mark.ecp
    def test_setitem_is_equivalent_to_set(self):
        via_setitem = LRUCache(2)
        via_set = LRUCache(2)
        for key in ["a", "b", "c"]:
            via_setitem[key] = 1
            via_set.set(key, 1)
        assert via_setitem.lru == via_set.lru


class TestDelete:
    @pytest.mark.ecp
    def test_delitem_removes_key(self):
        cache = filled(3, ["a", "b"])
        del cache["a"]
        assert "a" not in cache
        assert len(cache) == 1

    @pytest.mark.negative
    def test_delitem_missing_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            del LRUCache(2)["missing"]

    @pytest.mark.ecp
    def test_delitem_frees_a_slot_so_no_eviction_happens(self):
        cache = filled(2, ["a", "b"])
        del cache["a"]
        cache.set("c", 2)
        assert cache.lru == ["b", "c"]

    @pytest.mark.ecp
    def test_deleting_every_key_leaves_empty_cache(self):
        cache = filled(3, ["a", "b", "c"])
        for key in ["a", "b", "c"]:
            del cache[key]
        assert len(cache) == 0
        assert cache.lru == []

    @pytest.mark.ecp
    def test_pop_returns_value_and_removes_key(self):
        cache = filled(3, ["a", "b"])
        assert cache.pop("b") == 1
        assert "b" not in cache


class TestClear:
    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_clear_removes_all_items(self):
        cache = filled(3, ["a", "b", "c"])
        cache.clear()
        assert len(cache) == 0

    @pytest.mark.bva
    def test_clear_on_empty_cache_is_a_noop(self):
        cache = LRUCache(3)
        cache.clear()
        assert cache.lru == []

    @pytest.mark.ecp
    def test_cache_is_usable_after_clear(self):
        cache = filled(2, ["a", "b"])
        cache.clear()
        cache.set("z", 1)
        assert cache["z"] == 1

    @pytest.mark.ecp
    def test_clear_keeps_the_capacity_limit(self):
        cache = filled(2, ["a", "b"])
        cache.clear()
        for key in ["x", "y", "z"]:
            cache.set(key, 0)
        assert cache.lru == ["y", "z"]

    @pytest.mark.ecp
    def test_clear_does_not_touch_other_instances(self):
        first = filled(2, ["a"])
        second = filled(2, ["a"])
        first.clear()
        assert second.lru == ["a"]


class TestInspection:
    @pytest.mark.ecp
    def test_lru_lists_oldest_key_first(self):
        assert filled(3, ["a", "b", "c"]).lru == ["a", "b", "c"]

    @pytest.mark.ecp
    def test_lru_returns_a_copy_not_the_internal_state(self):
        cache = filled(3, ["a", "b"])
        cache.lru.append("hacked")
        assert cache.lru == ["a", "b"]

    @pytest.mark.bva
    @pytest.mark.parametrize("count", [0, 1, 2])
    def test_length_matches_number_of_items(self, count):
        cache = filled(5, [f"k{i}" for i in range(count)])
        assert cache.length == count
        assert len(cache) == count

    @pytest.mark.ecp
    def test_contains_true_for_present_and_false_for_absent_key(self):
        cache = filled(3, ["a"])
        assert "a" in cache
        assert "b" not in cache

    @pytest.mark.ecp
    def test_contains_does_not_refresh_recency(self):
        cache = filled(2, ["a", "b"])
        assert "a" in cache
        cache.set("c", 2)
        assert "a" not in cache

    @pytest.mark.ecp
    def test_iteration_follows_lru_order(self):
        assert list(filled(3, ["a", "b", "c"])) == ["a", "b", "c"]

    @pytest.mark.ecp
    def test_update_inherited_from_mutablemapping_respects_capacity(self):
        cache = LRUCache(2)
        cache.update({"a": 1, "b": 2, "c": 3})
        assert cache.lru == ["b", "c"]

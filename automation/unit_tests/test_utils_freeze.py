"""
Module 1, functions freeze() and FrozenDict (tinydb/utils.py)

Owner: Musab Butt

Techniques: ECP, BVA. See docs/ECP_BVA_NOTES.md section 1.
"""
import pytest

from tinydb.utils import FrozenDict, freeze

pytestmark = pytest.mark.utils


class TestFreeze:
    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_freeze_dict_returns_frozendict(self):
        assert isinstance(freeze({"a": 1}), FrozenDict)

    @pytest.mark.ecp
    def test_freeze_list_returns_tuple(self):
        assert freeze([1, 2, 3]) == (1, 2, 3)

    @pytest.mark.ecp
    def test_freeze_tuple_freezes_nested_list(self):
        assert freeze((1, [2, 3])) == (1, (2, 3))

    @pytest.mark.ecp
    def test_freeze_set_returns_frozenset(self):
        result = freeze({1, 2})
        assert isinstance(result, frozenset)
        assert result == frozenset({1, 2})

    @pytest.mark.ecp
    @pytest.mark.parametrize("scalar", [1, 2.5, "text", None, True])
    def test_freeze_passes_scalars_through_unchanged(self, scalar):
        assert freeze(scalar) is scalar

    @pytest.mark.ecp
    def test_freeze_is_recursive_through_dict_and_list(self):
        frozen = freeze({"a": [1, {"b": [2]}]})
        assert frozen["a"] == (1, {"b": (2,)})
        assert isinstance(frozen["a"][1], FrozenDict)

    @pytest.mark.bva
    def test_freeze_empty_containers(self):
        assert freeze({}) == {}
        assert freeze([]) == ()
        assert freeze(()) == ()
        assert freeze(set()) == frozenset()

    @pytest.mark.ecp
    def test_frozen_nested_structure_is_hashable(self):
        assert isinstance(hash(freeze({"a": [1, 2], "b": {"c": [3]}})), int)

    @pytest.mark.ecp
    def test_freeze_does_not_modify_the_original(self):
        original = {"a": [1, 2]}
        freeze(original)
        assert original == {"a": [1, 2]}
        assert isinstance(original["a"], list)


class TestFrozenDict:
    @pytest.mark.ecp
    def test_equal_dicts_have_equal_hashes_regardless_of_insertion_order(self):
        first = FrozenDict([("a", 1), ("b", 2)])
        second = FrozenDict([("b", 2), ("a", 1)])
        assert hash(first) == hash(second)

    @pytest.mark.ecp
    def test_different_dicts_have_different_hashes(self):
        assert hash(FrozenDict(a=1)) != hash(FrozenDict(a=2))

    @pytest.mark.ecp
    def test_frozendict_can_be_used_as_dict_key(self):
        key = FrozenDict(a=1)
        assert {key: "value"}[FrozenDict(a=1)] == "value"

    @pytest.mark.ecp
    def test_reading_still_works(self):
        frozen = FrozenDict(a=1)
        assert frozen["a"] == 1
        assert frozen.get("zzz") is None
        assert len(frozen) == 1

    @pytest.mark.negative
    @pytest.mark.parametrize(
        "mutation",
        [
            lambda d: d.__setitem__("a", 2),
            lambda d: d.__delitem__("a"),
            lambda d: d.clear(),
            lambda d: d.setdefault("z", 1),
            lambda d: d.popitem(),
            lambda d: d.update({"a": 2}),
            lambda d: d.pop("a"),
        ],
        ids=["setitem", "delitem", "clear", "setdefault", "popitem", "update", "pop"],
    )
    def test_every_mutation_raises_typeerror(self, mutation):
        frozen = FrozenDict(a=1)
        with pytest.raises(TypeError):
            mutation(frozen)
        assert frozen == {"a": 1}

    @pytest.mark.bva
    def test_empty_frozendict_is_hashable(self):
        assert isinstance(hash(FrozenDict()), int)

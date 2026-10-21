"""
Module 2, classes Query and QueryInstance (tinydb/queries.py)

Owner: Huzaifa Imran

Techniques: ECP, BVA. See docs/ECP_BVA_NOTES.md section 2.
Functions covered: ==, !=, <, <=, >, >=, exists, matches, search, test, any,
all, one_of, fragment, noop, map, path building, &, |, ~.
"""
import re

import pytest

from tinydb.queries import Query, QueryInstance, where

pytestmark = pytest.mark.queries


class TestPathBuilding:
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_evaluating_an_empty_query_raises_runtimeerror(self):
        with pytest.raises(RuntimeError):
            Query()({})

    @pytest.mark.negative
    def test_operator_without_a_path_raises_valueerror(self):
        with pytest.raises(ValueError):
            Query() == 1

    @pytest.mark.ecp
    def test_attribute_access_builds_nested_path(self):
        assert (Query().a.b == 1)({"a": {"b": 1}})

    @pytest.mark.ecp
    def test_item_access_builds_the_same_path_as_attribute_access(self):
        document = {"a": {"b": 1}}
        assert (Query()["a"]["b"] == 1)(document) == (Query().a.b == 1)(document)

    @pytest.mark.ecp
    def test_where_is_shorthand_for_item_access(self):
        assert (where("a") == 1)({"a": 1})

    @pytest.mark.ecp
    def test_item_access_can_reach_a_field_named_like_a_method(self):
        assert (Query()["test"] == 1)({"test": 1})

    @pytest.mark.ecp
    def test_missing_intermediate_key_evaluates_to_false(self):
        assert not (Query().a.b == 1)({"x": 1})

    @pytest.mark.ecp
    def test_path_through_a_non_mapping_evaluates_to_false(self):
        assert not (Query().a.b == 1)({"a": 5})


class TestComparison:
    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_eq_matches_equal_value_only(self):
        query = where("age") == 30
        assert query({"age": 30})
        assert not query({"age": 31})

    @pytest.mark.ecp
    def test_ne_matches_different_value_only(self):
        query = where("age") != 30
        assert query({"age": 31})
        assert not query({"age": 30})

    @pytest.mark.ecp
    def test_missing_field_never_matches_eq(self):
        assert not (where("age") == 30)({"name": "x"})

    @pytest.mark.ecp
    def test_missing_field_never_matches_ne(self):
        assert not (where("age") != 30)({"name": "x"})

    @pytest.mark.bva
    @pytest.mark.parametrize(
        "age, expected", [(17, False), (18, True), (19, True)]
    )
    def test_ge_boundary_at_18(self, age, expected):
        assert bool((where("age") >= 18)({"age": age})) is expected

    @pytest.mark.bva
    @pytest.mark.parametrize(
        "age, expected", [(17, True), (18, False), (19, False)]
    )
    def test_lt_boundary_at_18(self, age, expected):
        assert bool((where("age") < 18)({"age": age})) is expected

    @pytest.mark.bva
    @pytest.mark.parametrize(
        "age, expected", [(17, True), (18, True), (19, False)]
    )
    def test_le_boundary_at_18(self, age, expected):
        assert bool((where("age") <= 18)({"age": age})) is expected

    @pytest.mark.bva
    @pytest.mark.parametrize(
        "age, expected", [(17, False), (18, False), (19, True)]
    )
    def test_gt_boundary_at_18(self, age, expected):
        assert bool((where("age") > 18)({"age": age})) is expected

    @pytest.mark.ecp
    def test_float_and_int_compare_numerically(self):
        assert (where("n") == 1)({"n": 1.0})
        assert (where("n") > 1)({"n": 1.5})

    @pytest.mark.negative
    def test_incomparable_types_raise_typeerror_from_the_test(self):
        # TinyDB only swallows KeyError and TypeError while resolving the
        # path, not while running the comparison itself.
        with pytest.raises(TypeError):
            (where("age") > 18)({"age": "old"})


class TestExists:
    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_exists_true_when_key_present(self):
        assert where("a").exists()({"a": 1})

    @pytest.mark.ecp
    def test_exists_false_when_key_absent(self):
        assert not where("a").exists()({"b": 1})

    @pytest.mark.ecp
    def test_exists_true_when_value_is_none(self):
        assert where("a").exists()({"a": None})

    @pytest.mark.ecp
    def test_exists_works_on_nested_path(self):
        assert Query().a.b.exists()({"a": {"b": 0}})
        assert not Query().a.b.exists()({"a": {}})

    @pytest.mark.bva
    def test_exists_on_empty_document_is_false(self):
        assert not where("a").exists()({})


class TestMatchesAndSearch:
    @pytest.mark.ecp
    def test_matches_full_pattern(self):
        assert where("s").matches(r"^\d+$")({"s": "123"})

    @pytest.mark.ecp
    def test_matches_rejects_non_matching_string(self):
        assert not where("s").matches(r"^\d+$")({"s": "12a"})

    @pytest.mark.ecp
    def test_matches_anchors_at_the_start_only(self):
        # re.match semantics: a prefix match is enough (differs from the
        # docstring, which says the whole string must match)
        assert where("s").matches(r"\d+")({"s": "123abc"})
        assert not where("s").matches(r"\d+")({"s": "abc123"})

    @pytest.mark.negative
    @pytest.mark.parametrize("value", [123, None, ["1"], 1.5])
    def test_matches_non_string_value_is_false(self, value):
        assert not where("s").matches(r".*")({"s": value})

    @pytest.mark.ecp
    def test_matches_honours_regex_flags(self):
        assert where("s").matches("abc", re.IGNORECASE)({"s": "ABC"})
        assert not where("s").matches("abc")({"s": "ABC"})

    @pytest.mark.ecp
    def test_search_finds_pattern_anywhere(self):
        assert where("s").search(r"\d+")({"s": "abc123def"})

    @pytest.mark.ecp
    def test_search_false_when_pattern_absent(self):
        assert not where("s").search(r"\d+")({"s": "abc"})

    @pytest.mark.negative
    def test_search_non_string_value_is_false(self):
        assert not where("s").search(r"\d+")({"s": 42})

    @pytest.mark.bva
    def test_matches_empty_string_against_star_pattern(self):
        assert where("s").matches(r".*")({"s": ""})
        assert not where("s").matches(r".+")({"s": ""})


class TestCustomTest:
    @pytest.mark.ecp
    def test_test_runs_the_function_on_the_field_value(self):
        assert where("n").test(lambda v: v % 2 == 0)({"n": 4})
        assert not where("n").test(lambda v: v % 2 == 0)({"n": 3})

    @pytest.mark.ecp
    def test_test_forwards_extra_arguments(self):
        assert where("n").test(lambda v, low, high: low <= v <= high, 1, 5)({"n": 3})
        assert not where("n").test(lambda v, low, high: low <= v <= high, 1, 5)({"n": 6})

    @pytest.mark.ecp
    def test_test_on_missing_field_is_false_without_calling_the_function(self):
        calls = []
        query = where("n").test(lambda v: calls.append(v) or True)
        assert not query({"x": 1})
        assert calls == []

    @pytest.mark.ecp
    def test_map_applies_a_function_to_the_path_value(self):
        assert (where("name").map(len) == 3)({"name": "abc"})

    @pytest.mark.ecp
    def test_map_makes_the_query_uncacheable(self):
        assert not (where("name").map(len) == 3).is_cacheable()


class TestSequenceQueries:
    @pytest.mark.ecp
    def test_any_with_list_matches_when_one_element_overlaps(self):
        assert where("l").any([1, 2, 3])({"l": [3, 4, 5]})

    @pytest.mark.ecp
    def test_any_with_list_false_when_no_overlap(self):
        assert not where("l").any([1, 2])({"l": [8, 9]})

    @pytest.mark.ecp
    def test_any_with_subquery(self):
        query = where("l").any(where("x") == 1)
        assert query({"l": [{"x": 0}, {"x": 1}]})
        assert not query({"l": [{"x": 0}, {"x": 2}]})

    @pytest.mark.bva
    def test_any_on_empty_list_is_false(self):
        assert not where("l").any([1])({"l": []})

    @pytest.mark.negative
    def test_any_on_a_string_value_is_false(self):
        assert not where("l").any(["a"])({"l": "abc"})

    @pytest.mark.ecp
    def test_all_with_list_requires_every_item_present(self):
        assert where("l").all([1, 2])({"l": [1, 2, 3]})
        assert not where("l").all([1, 9])({"l": [1, 2, 3]})

    @pytest.mark.ecp
    def test_all_with_subquery(self):
        query = where("l").all(where("x") == 1)
        assert query({"l": [{"x": 1}, {"x": 1}]})
        assert not query({"l": [{"x": 1}, {"x": 2}]})

    @pytest.mark.bva
    def test_all_with_subquery_on_empty_list_is_vacuously_true(self):
        assert where("l").all(where("x") == 1)({"l": []})

    @pytest.mark.bva
    def test_all_with_empty_required_list_is_true(self):
        assert where("l").all([])({"l": [1]})

    @pytest.mark.ecp
    def test_one_of_matches_value_in_list(self):
        query = where("c").one_of(["red", "blue"])
        assert query({"c": "red"})
        assert not query({"c": "green"})

    @pytest.mark.bva
    def test_one_of_with_empty_list_never_matches(self):
        assert not where("c").one_of([])({"c": "red"})


class TestFragmentAndNoop:
    @pytest.mark.ecp
    def test_fragment_matches_when_all_fragment_keys_equal(self):
        assert Query().fragment({"a": 1})({"a": 1, "b": 2})

    @pytest.mark.ecp
    def test_fragment_false_on_value_mismatch(self):
        assert not Query().fragment({"a": 1})({"a": 2, "b": 2})

    @pytest.mark.ecp
    def test_fragment_false_when_key_missing(self):
        assert not Query().fragment({"a": 1})({"b": 2})

    @pytest.mark.bva
    def test_empty_fragment_matches_every_document(self):
        assert Query().fragment({})({"anything": 1})

    @pytest.mark.ecp
    def test_noop_always_true(self):
        assert Query().noop()({})
        assert Query().noop()({"a": 1})

    @pytest.mark.ecp
    def test_noop_is_neutral_when_combined_with_and(self):
        base = Query().noop()
        combined = base & (where("a") == 1)
        assert combined({"a": 1})
        assert not combined({"a": 2})


class TestCombinators:
    @pytest.mark.smoke
    @pytest.mark.ecp
    @pytest.mark.parametrize(
        "document, expected",
        [
            ({"a": 1, "b": 2}, True),
            ({"a": 1, "b": 0}, False),
            ({"a": 0, "b": 2}, False),
            ({"a": 0, "b": 0}, False),
        ],
    )
    def test_and_truth_table(self, document, expected):
        query = (where("a") == 1) & (where("b") == 2)
        assert bool(query(document)) is expected

    @pytest.mark.ecp
    @pytest.mark.parametrize(
        "document, expected",
        [
            ({"a": 1, "b": 2}, True),
            ({"a": 1, "b": 0}, True),
            ({"a": 0, "b": 2}, True),
            ({"a": 0, "b": 0}, False),
        ],
    )
    def test_or_truth_table(self, document, expected):
        query = (where("a") == 1) | (where("b") == 2)
        assert bool(query(document)) is expected

    @pytest.mark.ecp
    def test_not_inverts_result(self):
        query = ~(where("a") == 1)
        assert query({"a": 2})
        assert not query({"a": 1})

    @pytest.mark.ecp
    def test_double_negation_restores_result(self):
        query = ~~(where("a") == 1)
        assert query({"a": 1})
        assert not query({"a": 2})

    @pytest.mark.ecp
    def test_combining_returns_a_queryinstance(self):
        assert isinstance((where("a") == 1) & (where("b") == 2), QueryInstance)


class TestHashingAndCaching:
    @pytest.mark.ecp
    def test_same_query_has_same_hash_and_is_equal(self):
        assert hash(where("a") == 1) == hash(where("a") == 1)
        assert (where("a") == 1) == (where("a") == 1)

    @pytest.mark.ecp
    def test_different_value_gives_different_query(self):
        assert (where("a") == 1) != (where("a") == 2)

    @pytest.mark.ecp
    def test_and_is_commutative_for_equality_and_hash(self):
        first = (where("a") == 1) & (where("b") == 2)
        second = (where("b") == 2) & (where("a") == 1)
        assert first == second
        assert hash(first) == hash(second)

    @pytest.mark.ecp
    def test_or_is_commutative_for_equality(self):
        first = (where("a") == 1) | (where("b") == 2)
        second = (where("b") == 2) | (where("a") == 1)
        assert first == second

    @pytest.mark.ecp
    def test_plain_comparison_query_is_cacheable(self):
        assert (where("a") == 1).is_cacheable()

    @pytest.mark.ecp
    def test_uncacheable_part_makes_a_combined_query_uncacheable(self):
        combined = (where("a").map(len) == 1) & (where("b") == 2)
        assert not combined.is_cacheable()

    @pytest.mark.ecp
    def test_queryinstance_is_not_equal_to_other_types(self):
        assert (where("a") == 1) != "a == 1"

    @pytest.mark.ecp
    def test_regex_flags_change_the_query_identity(self):
        assert where("s").matches("a", 0) != where("s").matches("a", re.IGNORECASE)

    @pytest.mark.ecp
    def test_repr_of_empty_query(self):
        assert repr(Query()) == "Query()"

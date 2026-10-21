"""
Shared fixtures and the execution order configuration.

Execution order
---------------
Groups run in this order: smoke, ecp, bva, negative, datadriven.
Inside a group, tests with @pytest.mark.run_order(n) run by ascending n,
then everything else keeps its natural (file and definition) order.

With pytest-xdist (-n) every worker collects tests in the same order, so the
group order is preserved per worker. A strictly serial run (no -n) guarantees
the global order.
"""
import pytest

from tinydb.storages import MemoryStorage

GROUP_ORDER = ["smoke", "ecp", "bva", "negative", "datadriven"]


def pytest_collection_modifyitems(config, items):
    def sort_key(item):
        group_rank = len(GROUP_ORDER)
        for rank, name in enumerate(GROUP_ORDER):
            if item.get_closest_marker(name):
                group_rank = rank
                break

        order_marker = item.get_closest_marker("run_order")
        order_value = order_marker.args[0] if order_marker else 0
        return (group_rank, order_value)

    # list.sort is stable, so equal keys keep their collection order
    items.sort(key=sort_key)


class CountingMemoryStorage(MemoryStorage):
    """MemoryStorage that counts how often write() reaches the storage."""

    def __init__(self):
        super().__init__()
        self.write_count = 0

    def write(self, data):
        self.write_count += 1
        super().write(data)


@pytest.fixture
def counting_storage_cls():
    return CountingMemoryStorage

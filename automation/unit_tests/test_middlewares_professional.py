import pytest

from tinydb import TinyDB
from tinydb.middlewares import CachingMiddleware, Middleware
from tinydb.storages import JSONStorage, MemoryStorage

pytestmark = pytest.mark.middleware


def make_cache(storage_cls, size=None):
    middleware = CachingMiddleware(storage_cls)()
    if size is not None:
        # WRITE_CACHE_SIZE is looked up on the instance, so this override
        # affects only this middleware
        middleware.WRITE_CACHE_SIZE = size
    return middleware


class TestMiddlewareBase:
    """Tests the base Middleware: storage creation, attribute forwarding, and nesting."""

    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_call_creates_the_storage_and_returns_the_middleware(self):
        middleware = Middleware(MemoryStorage)
        assert middleware.storage is None
        returned = middleware()
        assert returned is middleware
        assert isinstance(middleware.storage, MemoryStorage)

    @pytest.mark.ecp
    def test_unknown_attributes_are_forwarded_to_the_storage(self):
        middleware = Middleware(MemoryStorage)()
        middleware.storage.memory = {"x": 1}
        assert middleware.memory == {"x": 1}

    @pytest.mark.ecp
    def test_read_is_forwarded_to_the_storage(self):
        middleware = Middleware(MemoryStorage)()
        assert middleware.read() is None
        middleware.write({"a": 1})
        assert middleware.read() == {"a": 1}

    @pytest.mark.negative
    def test_forwarding_a_missing_attribute_raises_attributeerror(self):
        middleware = Middleware(MemoryStorage)()
        with pytest.raises(AttributeError):
            middleware.does_not_exist

    @pytest.mark.ecp
    def test_call_forwards_constructor_arguments(self, tmp_path):
        path = tmp_path / "db.json"
        middleware = Middleware(JSONStorage)(str(path))
        assert path.exists()
        middleware.close()

    @pytest.mark.ecp
    def test_middlewares_can_be_nested(self):
        outer = Middleware(CachingMiddleware(MemoryStorage))()
        assert isinstance(outer.storage, CachingMiddleware)
        assert isinstance(outer.storage.storage, MemoryStorage)


class TestCachingRead:
    """Tests cached reads, initial reads from storage, empty results, and behavior after closing."""

    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_first_read_of_empty_storage_returns_none(self):
        assert make_cache(MemoryStorage).read() is None

    @pytest.mark.ecp
    def test_read_serves_from_cache_after_the_first_read(self):
        middleware = make_cache(MemoryStorage)
        middleware.storage.memory = {"original": True}
        middleware.read()
        middleware.storage.memory = {"changed": True}
        assert middleware.read() == {"original": True}

    @pytest.mark.bva
    def test_empty_storage_is_not_cached_so_it_is_read_again(self):
        # An empty storage returns None, and None means "cache empty", so the
        # middleware asks the storage again on the next read.
        middleware = make_cache(MemoryStorage)
        assert middleware.read() is None
        middleware.storage.memory = {"late": True}
        assert middleware.read() == {"late": True}

    @pytest.mark.ecp
    def test_read_loads_existing_storage_content(self):
        middleware = make_cache(MemoryStorage)
        middleware.storage.memory = {"a": 1}
        assert middleware.read() == {"a": 1}

    @pytest.mark.ecp
    def test_read_returns_what_was_last_written(self):
        middleware = make_cache(MemoryStorage)
        middleware.write({"a": 1})
        assert middleware.read() == {"a": 1}

    @pytest.mark.ecp
    def test_read_returns_the_latest_of_several_writes(self):
        middleware = make_cache(MemoryStorage)
        middleware.write({"a": 1})
        middleware.write({"b": 2})
        assert middleware.read() == {"b": 2}

    @pytest.mark.negative
    def test_read_after_close_raises_valueerror(self):
        middleware = make_cache(MemoryStorage)
        middleware.close()
        with pytest.raises(ValueError):
            middleware.read()


class TestCachingWrite:
    """Tests buffered writes and the cache threshold at which data is flushed to storage."""

    @pytest.mark.ecp
    def test_write_goes_to_cache_not_to_storage(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.write({"a": 1})
        assert middleware.storage.write_count == 0
        assert middleware.storage.memory is None

    @pytest.mark.bva
    @pytest.mark.parametrize("size", [1, 2, 3, 5])
    def test_write_below_threshold_does_not_flush(self, counting_storage_cls, size):
        middleware = make_cache(counting_storage_cls, size)
        for index in range(size - 1):
            middleware.write({"n": index})
        assert middleware.storage.write_count == 0

    @pytest.mark.bva
    @pytest.mark.parametrize("size", [1, 2, 3, 5])
    def test_write_at_threshold_flushes_exactly_once(self, counting_storage_cls, size):
        middleware = make_cache(counting_storage_cls, size)
        for index in range(size):
            middleware.write({"n": index})
        assert middleware.storage.write_count == 1
        assert middleware.storage.memory == {"n": size - 1}

    @pytest.mark.bva
    def test_write_one_past_threshold_starts_a_new_batch(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls, 3)
        for index in range(4):
            middleware.write({"n": index})
        assert middleware.storage.write_count == 1
        assert middleware._cache_modified_count == 1

    @pytest.mark.negative
    def test_write_after_close_raises_valueerror(self):
        middleware = make_cache(MemoryStorage)
        middleware.close()
        with pytest.raises(ValueError):
            middleware.write({"a": 1})


class TestCachingFlush:
    """Tests explicit flushing, no-op flushes, modification-counter reset, and closed-state behavior."""

    @pytest.mark.run_order(1)
    @pytest.mark.ecp
    def test_flush_writes_pending_data_to_storage(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.write({"a": 1})
        middleware.flush()
        assert middleware.storage.memory == {"a": 1}
        assert middleware.storage.write_count == 1

    @pytest.mark.run_order(2)
    @pytest.mark.bva
    def test_flush_without_pending_writes_does_nothing(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.flush()
        assert middleware.storage.write_count == 0

    @pytest.mark.run_order(3)
    @pytest.mark.ecp
    def test_second_flush_without_new_writes_does_nothing(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.write({"a": 1})
        middleware.flush()
        middleware.flush()
        assert middleware.storage.write_count == 1

    @pytest.mark.run_order(4)
    @pytest.mark.ecp
    def test_flush_resets_the_modified_counter(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.write({"a": 1})
        middleware.flush()
        assert middleware._cache_modified_count == 0

    @pytest.mark.run_order(5)
    @pytest.mark.negative
    def test_flush_after_close_raises_valueerror(self):
        middleware = make_cache(MemoryStorage)
        middleware.close()
        with pytest.raises(ValueError):
            middleware.flush()

    @pytest.mark.run_order(6)
    @pytest.mark.ecp
    def test_flush_persists_only_the_latest_of_several_writes(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.write({"a": 1})
        middleware.write({"b": 2})
        middleware.flush()
        assert middleware.storage.memory == {"b": 2}
        assert middleware.storage.write_count == 1

    @pytest.mark.run_order(7)
    @pytest.mark.bva
    def test_flush_right_after_a_threshold_flush_does_nothing(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls, 2)
        middleware.write({"n": 0})
        middleware.write({"n": 1})
        middleware.flush()
        assert middleware.storage.write_count == 1


class TestCachingClose:
    """Tests persistence and cleanup when the middleware is closed."""

    @pytest.mark.ecp
    def test_close_flushes_pending_writes(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        middleware.write({"a": 1})
        storage = middleware.storage
        middleware.close()
        assert storage.memory == {"a": 1}

    @pytest.mark.ecp
    def test_close_without_pending_writes_does_not_write(self, counting_storage_cls):
        middleware = make_cache(counting_storage_cls)
        storage = middleware.storage
        middleware.close()
        assert storage.write_count == 0

    @pytest.mark.ecp
    def test_close_is_idempotent(self):
        middleware = make_cache(MemoryStorage)
        middleware.close()
        middleware.close()

    @pytest.mark.ecp
    def test_close_drops_the_cache(self):
        middleware = make_cache(MemoryStorage)
        middleware.write({"a": 1})
        middleware.close()
        assert middleware.cache is None

    @pytest.mark.ecp
    def test_close_closes_the_underlying_storage(self, tmp_path):
        middleware = CachingMiddleware(JSONStorage)(str(tmp_path / "db.json"))
        handle = middleware.storage._handle
        middleware.close()
        assert handle.closed


class TestCachingWithTinyDB:
    """Tests end-to-end behavior when CachingMiddleware is used through TinyDB."""

    @pytest.mark.smoke
    @pytest.mark.ecp
    def test_documents_are_readable_through_the_cache(self):
        db = TinyDB(storage=CachingMiddleware(MemoryStorage))
        db.insert({"a": 1})
        assert db.all() == [{"a": 1}]

    @pytest.mark.ecp
    def test_json_file_is_only_written_on_close(self, tmp_path):
        path = tmp_path / "db.json"
        db = TinyDB(str(path), storage=CachingMiddleware(JSONStorage))
        db.insert({"a": 1})
        assert path.read_text() == ""
        db.close()
        assert '"a": 1' in path.read_text()

    @pytest.mark.ecp
    def test_data_survives_a_reopen_after_close(self, tmp_path):
        path = str(tmp_path / "db.json")
        db = TinyDB(path, storage=CachingMiddleware(JSONStorage))
        db.insert({"a": 1})
        db.close()
        reopened = TinyDB(path, storage=CachingMiddleware(JSONStorage))
        assert reopened.all() == [{"a": 1}]
        reopened.close()
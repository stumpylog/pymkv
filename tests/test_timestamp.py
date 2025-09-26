import pytest

from pymkv.Timestamp import Timestamp


class TestInitialization:
    """Tests for the Timestamp class __init__ method."""

    def test_init_with_string(self):
        """Test initializing Timestamp with a valid timestamp string."""
        ts = Timestamp.from_string("01:23:45.123456789")
        assert ts.hh == 1
        assert ts.mm == 23
        assert ts.ss == 45
        assert ts.nn == 123456789

    def test_init_with_int(self):
        """Test initializing Timestamp with an integer (seconds)."""
        # 3600s (1hr) + 1380s (23min) + 45s = 5025s
        ts = Timestamp.from_seconds(5025)
        assert ts.hh == 1
        assert ts.mm == 23
        assert ts.ss == 45
        assert ts.nn == 0

    def test_init_with_timestamp_object(self):
        """Test initializing Timestamp from another Timestamp object."""
        ts1 = Timestamp.from_string("02:30:15")
        ts2 = Timestamp.from_timestamp(ts1)
        assert ts1 == ts2

    def test_init_with_invalid_string(self):
        """Test that initializing with a malformed string raises ValueError."""
        with pytest.raises(ValueError):
            Timestamp.from_string("not-a-timestamp")

    def test_init_with_invalid_type(self):
        """Test that initializing with an unsupported type raises TypeError."""
        with pytest.raises(TypeError):
            Timestamp(None)

    def test_init_with_mm_ss(self):
        """Test initializing Timestamp with MM:SS format."""
        ts = Timestamp.from_string("23:45")
        assert ts.hh == 0
        assert ts.mm == 23
        assert ts.ss == 45
        assert ts.nn == 0
        assert str(ts) == "00:23:45"

    def test_init_with_zero_nanoseconds_explicit(self):
        """Test initializing Timestamp with explicit .0 nanoseconds."""
        ts = Timestamp.from_string("01:23:45.0")
        assert ts.hh == 1
        assert ts.mm == 23
        assert ts.ss == 45
        assert ts.nn == 0
        assert str(ts) == "01:23:45"


class TestComparisons:
    """Tests for the comparison methods of the Timestamp class."""

    @pytest.mark.parametrize(
        ("ts1_str", "ts2_str", "is_equal"),
        [
            pytest.param("01:01:01.1", "01:01:01.100000000", True, id="equal_different_ns_precision"),
            pytest.param("01:01:01.1", "01:01:01.2", False, id="unequal_ns"),
            pytest.param("01:01:01.0", "01:01:02.0", False, id="unequal_seconds"),
            pytest.param("01:01:00.0", "01:02:00.0", False, id="unequal_minutes"),
            pytest.param("01:00:00.0", "02:00:00.0", False, id="unequal_hours"),
        ],
    )
    def test_eq_ne(self, ts1_str: str, ts2_str: str, is_equal: bool):
        """Test equality (==) and inequality (!=) comparisons."""
        ts1 = Timestamp.from_string(ts1_str)
        ts2 = Timestamp.from_string(ts2_str)
        assert (ts1 == ts2) is is_equal
        assert (ts1 != ts2) is not is_equal

    @pytest.mark.parametrize(
        ("ts_smaller_str", "ts_larger_str"),
        [
            pytest.param("01:01:01.1", "01:01:01.2", id="compare_ns"),
            pytest.param("01:01:01.9", "01:01:02.0", id="compare_seconds"),
            pytest.param("01:01:59.0", "01:02:00.0", id="compare_minutes"),
            pytest.param("01:59:00.0", "02:00:00.0", id="compare_hours"),
        ],
    )
    def test_lt_gt(self, ts_smaller_str: str, ts_larger_str: str):
        """Test less than (<) and greater than (>) comparisons."""
        ts_smaller = Timestamp.from_string(ts_smaller_str)
        ts_larger = Timestamp.from_string(ts_larger_str)
        assert ts_smaller < ts_larger
        assert ts_larger > ts_smaller
        assert not (ts_larger < ts_smaller)
        assert not (ts_smaller > ts_larger)

    @pytest.mark.parametrize(
        ("ts_smaller_str", "ts_larger_str"),
        [
            pytest.param("01:01:01.1", "01:01:01.2", id="less_than"),
            pytest.param("01:01:01.1", "01:01:01.1", id="equal_to"),
        ],
    )
    def test_le_ge(self, ts_smaller_str: str, ts_larger_str: str):
        """Test less than or equal to (<=) and greater than or equal to (>=)."""
        ts_smaller = Timestamp.from_string(ts_smaller_str)
        ts_larger = Timestamp.from_string(ts_larger_str)
        assert ts_smaller <= ts_larger
        assert ts_larger >= ts_smaller
        if ts_smaller_str != ts_larger_str:
            assert not (ts_larger <= ts_smaller)
            assert not (ts_smaller >= ts_larger)


class TestDunderMethods:
    """Tests for other dunder methods in the Timestamp class."""

    def test_str(self):
        """Test the __str__ method."""
        ts = Timestamp.from_string("12:34:56.789")
        assert str(ts) == "12:34:56.789"

import pytest
from typing import Any
from pymkv.Timestamp import Timestamp

class TestInitialization:
    """Tests for the Timestamp class __init__ method."""

    def test_init_with_string(self):
        """Test initializing Timestamp with a valid timestamp string."""
        ts = Timestamp("01:23:45.123456789")
        assert ts.hh == 1
        assert ts.mm == 23
        assert ts.ss == 45
        assert ts.nn == 123456789

    def test_init_with_int(self):
        """Test initializing Timestamp with an integer (seconds)."""
        # 3600s (1hr) + 1380s (23min) + 45s = 5025s
        ts = Timestamp(5025)
        assert ts.hh == 1
        assert ts.mm == 23
        assert ts.ss == 45
        assert ts.nn == 0

    def test_init_with_timestamp_object(self):
        """Test initializing Timestamp from another Timestamp object."""
        ts1 = Timestamp("02:30:15")
        ts2 = Timestamp(ts1)
        assert ts1 == ts2

    def test_init_with_none(self):
        """Test initializing Timestamp with no timestamp value."""
        ts = Timestamp()
        assert ts.hh == 0
        assert ts.mm == 0
        assert ts.ss == 0
        assert ts.nn == 0

    @pytest.mark.xfail(reason="Values are not limited at construction time")
    def test_init_with_out_of_range_overrides(self):
        """Test that out-of-range overrides are set to 0."""
        ts = Timestamp(mm=61, ss=90, nn=1000000001)
        assert ts.mm == 0
        assert ts.ss == 0
        assert ts.nn == 0

    def test_init_with_overrides(self):
        """Test overriding parts of a timestamp during initialization."""
        ts = Timestamp("01:01:01.1", hh=2, mm=3, ss=4, nn=500000000)
        assert ts.hh == 2
        assert ts.mm == 3
        assert ts.ss == 4
        assert ts.nn == 500000000

    def test_init_with_invalid_string(self):
        """Test that initializing with a malformed string raises ValueError."""
        with pytest.raises(ValueError):
            Timestamp("not-a-timestamp")

    def test_init_with_invalid_type(self):
        """Test that initializing with an unsupported type raises TypeError."""
        with pytest.raises(TypeError):
            Timestamp(12.34)

class TestProperties:
    """Tests for the properties of the Timestamp class."""

    def test_ts_setter(self):
        """Test the ts property setter."""
        ts = Timestamp("01:01:01.1")
        ts.ts = "02:02:02.2"
        assert ts.hh == 2
        assert ts.mm == 2
        assert ts.ss == 2
        assert ts.nn == 200000000

        ts.ts = 3661
        assert ts.hh == 1
        assert ts.mm == 1
        assert ts.ss == 1
        assert ts.nn == 0

    def test_ts_setter_invalid_type(self):
        """Test that setting ts with an invalid type raises TypeError."""
        ts = Timestamp()
        with pytest.raises(TypeError):
            ts.ts = 12.34

    def test_individual_setters(self):
        """Test the individual setters for hh, mm, ss, and nn."""
        ts = Timestamp()
        ts.hh = 5
        ts.mm = 15
        ts.ss = 30
        ts.nn = 500000000
        assert ts.hh == 5
        assert ts.mm == 15
        assert ts.ss == 30
        assert ts.nn == 500000000

    def test_individual_setters_out_of_range(self):
        """Test that out-of-range values in setters are set to 0."""
        ts = Timestamp()
        ts.mm = 60
        ts.ss = 60
        ts.nn = 1000000000
        assert ts.mm == 0
        assert ts.ss == 0
        assert ts.nn == 0

    def test_form_property(self):
        """Test the form property getter and setter."""
        ts = Timestamp()
        assert ts.form == "MM:SS"
        ts.form = "HH:MM:SS"
        assert ts.form == "HH:MM:SS"

class TestComparisons:
    """Tests for the comparison methods of the Timestamp class."""

    @pytest.mark.parametrize(
        "ts1_str, ts2_str, is_equal",
        [
            pytest.param("01:01:01.1", "01:01:01.100000000", True, id="equal_different_ns_precision"),
            pytest.param("01:01:01.1", "01:01:01.2", False, id="unequal_ns"),
            pytest.param("01:01:01.0", "01:01:02.0", False, id="unequal_seconds"),
            pytest.param("01:01:00.0", "01:02:00.0", False, id="unequal_minutes"),
            pytest.param("01:00:00.0", "02:00:00.0", False, id="unequal_hours"),
        ]
    )
    def test_eq_ne(self, ts1_str: str, ts2_str: str, is_equal: bool):
        """Test equality (==) and inequality (!=) comparisons."""
        ts1 = Timestamp(ts1_str)
        ts2 = Timestamp(ts2_str)
        assert (ts1 == ts2) is is_equal
        assert (ts1 != ts2) is not is_equal

    @pytest.mark.parametrize(
        "ts_smaller_str, ts_larger_str",
        [
            pytest.param("01:01:01.1", "01:01:01.2", id="compare_ns"),
            pytest.param("01:01:01.9", "01:01:02.0", id="compare_seconds"),
            pytest.param("01:01:59.0", "01:02:00.0", id="compare_minutes"),
            pytest.param("01:59:00.0", "02:00:00.0", id="compare_hours"),
        ]
    )
    def test_lt_gt(self, ts_smaller_str: str, ts_larger_str: str):
        """Test less than (<) and greater than (>) comparisons."""
        ts_smaller = Timestamp(ts_smaller_str)
        ts_larger = Timestamp(ts_larger_str)
        assert ts_smaller < ts_larger
        assert ts_larger > ts_smaller
        assert not (ts_larger < ts_smaller)
        assert not (ts_smaller > ts_larger)

    @pytest.mark.parametrize(
        "ts_smaller_str, ts_larger_str",
        [
            pytest.param("01:01:01.1", "01:01:01.2", id="less_than"),
            pytest.param("01:01:01.1", "01:01:01.1", id="equal_to"),
        ]
    )
    def test_le_ge(self, ts_smaller_str: str, ts_larger_str: str):
        """Test less than or equal to (<=) and greater than or equal to (>=)."""
        ts_smaller = Timestamp(ts_smaller_str)
        ts_larger = Timestamp(ts_larger_str)
        assert ts_smaller <= ts_larger
        assert ts_larger >= ts_smaller
        if ts_smaller_str != ts_larger_str:
            assert not (ts_larger <= ts_smaller)
            assert not (ts_smaller >= ts_larger)

class TestDunderMethods:
    """Tests for other dunder methods in the Timestamp class."""

    def test_str(self):
        """Test the __str__ method."""
        ts = Timestamp("12:34:56.789", form="HH:MM:SS.NN")
        assert str(ts) == "12:34:56.789"

    def test_getitem(self):
        """Test the __getitem__ method."""
        ts = Timestamp(hh=1, mm=2, ss=3, nn=9)
        assert ts[0] == 1
        assert ts[1] == 2
        assert ts[2] == 3
        assert ts[3] == 9

class TestStaticMethods:
    """Tests for static methods in the Timestamp class."""

    @pytest.mark.parametrize(
        "timestamp_str",
        [
            pytest.param("1:2:3", id="h_m_s"),
            pytest.param("01:02:03", id="hh_mm_ss"),
            pytest.param("12:34:56.123456789", id="full_timestamp_with_ns"),
            pytest.param("59:59", id="mm_ss"),
            pytest.param("1:2", id="m_s"),
        ]
    )
    def test_verify_valid(self, timestamp_str: str):
        """Test Timestamp.verify with valid timestamp strings."""
        assert Timestamp.verify(timestamp_str) is True

    @pytest.mark.parametrize(
        "timestamp_str",
        [
            pytest.param("1:2:3:4", id="too_many_colons"),
            pytest.param("12:34:56.", id="trailing_dot"),
            pytest.param("12:34:56.1234567890", id="too_many_ns_digits"),
            pytest.param("timestamp", id="non_numeric_string"),
        ]
    )
    def test_verify_invalid(self, timestamp_str: str):
        """Test Timestamp.verify with invalid timestamp strings."""
        assert Timestamp.verify(timestamp_str) is False

    def test_verify_invalid_type(self):
        """Test that Timestamp.verify raises TypeError for non-string input."""
        with pytest.raises(TypeError):
            Timestamp.verify(123)
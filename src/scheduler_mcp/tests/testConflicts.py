"""
Tests for time conflict detection functionality.
"""

import pytest
from datetime import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scheduler_mcp import schueduling


def test_parse_time_12hour():
    """Test parsing 12-hour time format."""
    result = schueduling.parse_time("10:00 AM")
    
    assert result == time(10, 0)


def test_parse_time_12hour_pm():
    """Test parsing 12-hour PM time format."""
    result = schueduling.parse_time("2:30 PM")
    
    assert result == time(14, 30)


def test_parse_time_24hour():
    """Test parsing 24-hour time format."""
    result = schueduling.parse_time("14:30")
    
    assert result == time(14, 30)


def test_parse_time_invalid():
    """Test parsing invalid time format."""
    result = schueduling.parse_time("invalid")
    
    assert result is None


def test_parse_time_empty():
    """Test parsing empty time string."""
    result = schueduling.parse_time("")
    
    assert result is None


def test_times_overlap_yes():
    """Test overlapping time ranges."""
    start1 = time(10, 0)
    end1 = time(11, 0)
    start2 = time(10, 30)
    end2 = time(11, 30)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == True


def test_times_overlap_no():
    """Test non-overlapping time ranges."""
    start1 = time(10, 0)
    end1 = time(11, 0)
    start2 = time(11, 0)
    end2 = time(12, 0)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == False


def test_times_overlap_adjacent():
    """Test adjacent time ranges (should not overlap)."""
    start1 = time(10, 0)
    end1 = time(11, 0)
    start2 = time(11, 0)
    end2 = time(12, 0)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == False


def test_times_overlap_contained():
    """Test when one time range is contained in another."""
    start1 = time(10, 0)
    end1 = time(12, 0)
    start2 = time(10, 30)
    end2 = time(11, 30)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == True


def test_times_overlap_reverse():
    """Test overlapping time ranges in reverse order."""
    start1 = time(10, 30)
    end1 = time(11, 30)
    start2 = time(10, 0)
    end2 = time(11, 0)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == True


def test_times_overlap_exact_same():
    """Test exact same time ranges."""
    start1 = time(10, 0)
    end1 = time(11, 0)
    start2 = time(10, 0)
    end2 = time(11, 0)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == True


def test_times_overlap_one_minute():
    """Test time ranges overlapping by one minute."""
    start1 = time(10, 0)
    end1 = time(11, 0)
    start2 = time(10, 59)
    end2 = time(12, 0)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == True


def test_times_overlap_morning_afternoon():
    """Test non-overlapping morning and afternoon classes."""
    start1 = time(8, 0)
    end1 = time(10, 0)
    start2 = time(14, 0)
    end2 = time(16, 0)
    
    result = schueduling.times_overlap(start1, end1, start2, end2)
    
    assert result == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

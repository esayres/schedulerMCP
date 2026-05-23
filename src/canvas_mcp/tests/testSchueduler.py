"""
Tests for schedule generation and scoring functionality.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from canvas_mcp import database, schueduling, workload


@pytest.fixture(autouse=True)
def load_test_data():
    """Load course data before each test."""
    try:
        database.load_courses()
    except FileNotFoundError:
        pytest.skip("Course data not available")


def test_calculate_total_units():
    """Test unit calculation for courses."""
    courses = ["acct111", "acct115"]
    
    total = schueduling.calculate_total_units(courses)
    
    # acct111 is 3 units, acct115 is 2 units
    assert total == 5.0


def test_calculate_total_units_empty():
    """Test unit calculation with no courses."""
    courses = []
    
    total = schueduling.calculate_total_units(courses)
    
    assert total == 0.0


def test_generate_schedules_under_limit():
    """Test schedule generation when under unit limit."""
    courses = ["acct111", "acct115"]
    max_units = 18
    
    schedules = schueduling.generate_schedules(courses, max_units)
    
    assert len(schedules) > 0
    assert schedules[0]["valid"] == True
    assert schedules[0]["total_units"] <= max_units


def test_generate_schedules_over_limit():
    """Test schedule generation when over unit limit."""
    # Create a list of courses that exceeds the limit
    courses = ["acct111", "acct113", "acct115", "acct121", "acct131"]
    max_units = 5  # Very low limit
    
    schedules = schueduling.generate_schedules(courses, max_units)
    
    # Should return empty list when over limit
    assert len(schedules) == 0


def test_score_schedule_balanced():
    """Test schedule scoring with balanced preference."""
    courses = ["acct111", "acct115", "acct121"]
    
    score = schueduling.score_schedule(courses, "balanced")
    
    assert score > 0
    assert isinstance(score, float)


def test_score_schedule_compact():
    """Test schedule scoring with compact preference."""
    courses = ["acct111", "acct115"]
    
    score = schueduling.score_schedule(courses, "compact")
    
    assert score > 0


def test_score_schedule_no_mornings():
    """Test schedule scoring with no_mornings preference."""
    courses = ["acct111"]
    
    score = schueduling.score_schedule(courses, "no_mornings")
    
    assert score > 0


def test_detect_conflicts_empty():
    """Test conflict detection with no courses."""
    courses = []
    
    conflicts = schueduling.detect_conflicts(courses)
    
    assert len(conflicts) == 0


def test_detect_conflicts_single_course():
    """Test conflict detection with single course."""
    courses = ["acct111"]
    
    conflicts = schueduling.detect_conflicts(courses)
    
    assert len(conflicts) == 0


def test_estimate_workload():
    """Test workload estimation."""
    courses = ["acct111", "acct115"]
    
    result = workload.estimate_workload(courses)
    
    assert "total_weekly_hours" in result
    assert "assessment" in result
    assert "course_breakdown" in result
    assert result["total_weekly_hours"] > 0


def test_estimate_workload_empty():
    """Test workload estimation with no courses."""
    courses = []
    
    result = workload.estimate_workload(courses)
    
    assert result["total_weekly_hours"] == 0
    assert result["assessment"] == "light"


def test_calculate_difficulty_score():
    """Test difficulty score calculation."""
    score = workload.calculate_difficulty_score("acct111")
    
    assert 0 <= score <= 10
    assert isinstance(score, float)


def test_detect_heavy_semester():
    """Test heavy semester detection."""
    courses = ["acct111", "acct115", "acct121"]
    
    result = workload.detect_heavy_semester(courses)
    
    assert "is_heavy" in result
    assert "total_weekly_hours" in result
    assert "lab_course_count" in result
    assert "warnings" in result


def test_detect_deadline_clusters():
    """Test deadline cluster detection."""
    courses = ["acct111", "acct121"]
    
    result = workload.detect_deadline_clusters(courses)
    
    assert "high_workload_periods" in result
    assert "weekly_distribution" in result
    assert len(result["weekly_distribution"]) == 16  # 16 weeks


def test_search_courses():
    """Test course search functionality."""
    results = database.search_courses("accounting")
    
    assert len(results) > 0
    assert any("acct" in c["course_id"].lower() for c in results)


def test_search_courses_no_results():
    """Test course search with no matches."""
    results = database.search_courses("xyznonexistent")
    
    assert len(results) == 0


def test_get_course_by_id():
    """Test getting course by ID."""
    course = database.get_course_by_id("acct111")
    
    assert course is not None
    assert course["course_id"] == "acct111"
    assert "title" in course


def test_get_course_by_id_not_found():
    """Test getting non-existent course."""
    course = database.get_course_by_id("nonexistent999")
    
    assert course is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for prerequisite validation functionality.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from canvas_mcp import database, schueduling


@pytest.fixture(autouse=True)
def load_test_data():
    """Load course data before each test."""
    try:
        database.load_courses()
    except FileNotFoundError:
        pytest.skip("Course data not available")


def test_validate_prerequisites_satisfied():
    """Test prerequisite validation when all prerequisites are met."""
    completed = ["acct111"]
    requested = ["acct113"]
    
    result = schueduling.validate_prerequisites(completed, requested)
    
    assert result["valid"] == True
    assert len(result["missing_prerequisites"]) == 0
    assert "satisfied" in result["message"].lower()


def test_validate_prerequisites_missing():
    """Test prerequisite validation when prerequisites are missing."""
    completed = []
    requested = ["acct113"]
    
    result = schueduling.validate_prerequisites(completed, requested)
    
    assert result["valid"] == False
    assert len(result["missing_prerequisites"]) > 0
    assert "not satisfied" in result["message"].lower()


def test_validate_prerequisites_no_prereqs():
    """Test courses with no prerequisites."""
    completed = []
    requested = ["acct111"]
    
    result = schueduling.validate_prerequisites(completed, requested)
    
    assert result["valid"] == True
    assert len(result["missing_prerequisites"]) == 0


def test_validate_prerequisites_multiple_courses():
    """Test validation with multiple courses."""
    completed = ["acct111"]
    requested = ["acct113", "acct115"]
    
    result = schueduling.validate_prerequisites(completed, requested)
    
    # acct113 requires acct111 (satisfied)
    # acct115 has no prerequisites
    assert result["valid"] == True


def test_validate_prerequisites_case_insensitive():
    """Test that course IDs are case-insensitive."""
    completed = ["ACCT111"]
    requested = ["acct113"]
    
    result = schueduling.validate_prerequisites(completed, requested)
    
    assert result["valid"] == True


def test_validate_corequisites_satisfied():
    """Test corequisite validation when all corequisites are included."""
    # Find a course with corequisites in the dataset
    requested = ["acct111"]  # Assuming no coreqs for basic test
    
    result = schueduling.validate_corequisites(requested)
    
    assert result["valid"] == True
    assert len(result["missing_corequisites"]) == 0


def test_validate_corequisites_missing():
    """Test corequisite validation when corequisites are missing."""
    # This test would need a course with actual corequisites
    # For now, test the logic with a course that has no coreqs
    requested = ["acct111"]
    
    result = schueduling.validate_corequisites(requested)
    
    assert "valid" in result
    assert "missing_corequisites" in result


def test_validate_course_plan_valid():
    """Test multi-semester course plan validation with valid plan."""
    course_plan = [
        ["acct111"],           # Semester 1
        ["acct113", "acct115"] # Semester 2 (acct113 requires acct111)
    ]
    
    result = schueduling.validate_course_plan(course_plan)
    
    assert result["valid"] == True
    assert len(result["errors"]) == 0


def test_validate_course_plan_invalid():
    """Test multi-semester course plan validation with invalid plan."""
    course_plan = [
        ["acct113"],  # Semester 1 (requires acct111 but not taken yet)
        ["acct111"]   # Semester 2
    ]
    
    result = schueduling.validate_course_plan(course_plan)
    
    assert result["valid"] == False
    assert len(result["errors"]) > 0


def test_validate_course_plan_empty():
    """Test validation with empty course plan."""
    course_plan = []
    
    result = schueduling.validate_course_plan(course_plan)
    
    assert result["valid"] == True
    assert len(result["errors"]) == 0


def test_normalize_course_id():
    """Test course ID normalization."""
    assert database.normalize_course_id("ACCT111") == "acct111"
    assert database.normalize_course_id("acct111") == "acct111"
    assert database.normalize_course_id(" ACCT111 ") == "acct111"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

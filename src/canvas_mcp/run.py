"""
Main entry point for the MCP Scheduling Tool.

This module creates the FastMCP server and registers all scheduling tools.
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
from .tools import courses as course_tools

# Create MCP server instance
mcp = FastMCP("scheduler-mcp", log_level="DEBUG")


# =========================
# COURSE DATA TOOLS
# =========================

@mcp.tool()
def search_courses(query: str, semester: str = "fall_2026") -> List[Dict[str, Any]]:
    """
    Search courses by keyword, department, or course ID.
    
    Args:
        query: Search term (matches course ID, title, or description)
        semester: Semester identifier (default: "fall_2026")
    
    Returns:
        List of matching courses with basic information
    
    Example:
        search_courses("computer science")
        search_courses("MATH", "fall_2026")
    """
    return course_tools.search_courses_impl(query, semester)


@mcp.tool()
def get_course_info(course_id: str, semester: str = "fall_2026") -> Dict[str, Any]:
    """
    Get detailed information about a specific course.
    
    Args:
        course_id: Course identifier (e.g., "CS120", "MATH150")
        semester: Semester identifier (default: "fall_2026")
    
    Returns:
        Complete course information including prerequisites, units, and workload
    
    Example:
        get_course_info("acct111")
    """
    return course_tools.get_course_info_impl(course_id, semester)


@mcp.tool()
def get_course_sections(course_id: str, semester: str = "fall_2026") -> List[Dict[str, Any]]:
    """
    Get all available sections for a course.
    
    Note: Section data not yet available in current dataset.
    
    Args:
        course_id: Course identifier
        semester: Semester identifier (default: "fall_2026")
    
    Returns:
        List of course sections with meeting times
    """
    return course_tools.get_course_sections_impl(course_id, semester)


# =========================
# SCHEDULE ANALYSIS TOOLS
# =========================

@mcp.tool()
def detect_schedule_conflicts(course_ids: List[str]) -> Dict[str, Any]:
    """
    Detect time conflicts between selected courses.
    
    Args:
        course_ids: List of course IDs to check
    
    Returns:
        Conflict detection results
    
    Example:
        detect_schedule_conflicts(["cs120", "math150", "acct111"])
    """
    return course_tools.detect_schedule_conflicts_impl(course_ids)


@mcp.tool()
def generate_possible_schedules(
    requested_courses: List[str],
    max_units: int = 18
) -> List[Dict[str, Any]]:
    """
    Generate all valid schedule combinations from requested courses.
    
    Args:
        requested_courses: List of course IDs to schedule
        max_units: Maximum unit limit (default: 18)
    
    Returns:
        List of valid schedules with no conflicts
    
    Example:
        generate_possible_schedules(["cs120", "math150", "engl101"], max_units=15)
    """
    return course_tools.generate_possible_schedules_impl(requested_courses, max_units)


@mcp.tool()
def suggest_best_schedule(
    requested_courses: List[str],
    preference: str = "balanced",
    max_units: int = 18
) -> Dict[str, Any]:
    """
    Recommend the best schedule based on preferences.
    
    Args:
        requested_courses: List of course IDs to schedule
        preference: Preference type - "balanced", "compact", or "no_mornings"
        max_units: Maximum unit limit (default: 18)
    
    Returns:
        Best schedule recommendation with score
    
    Example:
        suggest_best_schedule(["cs120", "math150"], preference="no_mornings")
    """
    return course_tools.suggest_best_schedule_impl(requested_courses, preference, max_units)


# =========================
# PREREQUISITE VALIDATION TOOLS
# =========================

@mcp.tool()
def validate_prerequisites(
    completed_courses: List[str],
    requested_courses: List[str]
) -> Dict[str, Any]:
    """
    Validate that prerequisites are satisfied for requested courses.
    
    Args:
        completed_courses: List of already completed course IDs
        requested_courses: List of courses to validate
    
    Returns:
        Validation results with any missing prerequisites
    
    Example:
        validate_prerequisites(["acct111"], ["acct113"])
    """
    return course_tools.validate_prerequisites_impl(completed_courses, requested_courses)


@mcp.tool()
def validate_course_plan(course_plan: List[List[str]]) -> Dict[str, Any]:
    """
    Validate a multi-semester course plan.
    
    Args:
        course_plan: List of semesters, each containing course IDs
    
    Returns:
        Validation results for the entire plan
    
    Example:
        validate_course_plan([
            ["cs101", "math140"],
            ["cs120", "math150"],
            ["cs220", "cs240"]
        ])
    """
    return course_tools.validate_course_plan_impl(course_plan)


# =========================
# WORKLOAD ESTIMATION TOOLS
# =========================

@mcp.tool()
def estimate_semester_workload(course_ids: List[str]) -> Dict[str, Any]:
    """
    Estimate weekly workload for a schedule.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Workload breakdown with hours and assessment
    
    Example:
        estimate_semester_workload(["cs120", "math150", "phys201"])
    """
    return course_tools.estimate_semester_workload_impl(course_ids)


@mcp.tool()
def detect_deadline_clusters(course_ids: List[str]) -> Dict[str, Any]:
    """
    Predict weeks with heavy workload overlap.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Predicted high-workload weeks throughout the semester
    
    Example:
        detect_deadline_clusters(["cs120", "math150", "chem101"])
    """
    return course_tools.detect_deadline_clusters_impl(course_ids)


# =========================
# ENTRY POINT
# =========================

def main():
    """Start the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

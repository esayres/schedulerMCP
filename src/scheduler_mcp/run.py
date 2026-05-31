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
def run_scraper(semester: str = None, force: bool = False) -> Dict[str, Any]:
    """
    Run the web scraper to fetch and populate course data for a semester.
    
    WARNING: This takes 5-15 minutes to complete. The MCP call will timeout,
    but the scraper will continue running in the background.
    
    Args:
        semester: Semester identifier (e.g., "spring_2026", "fall_2026")
                 If None, uses current semester
        force: If True, re-scrape even if data already exists
    
    Returns:
        Status message about scraper execution
    
    Example:
        run_scraper("spring_2026")
    """
    from . import database, semesterSync
    import subprocess
    import sys
    from pathlib import Path
    
    # Determine semester
    if semester is None:
        semester = database.get_selected_semester()
    
    # Check if data already exists
    semester_path = Path(__file__).parent.parent.parent.parent / f"courses_{semester}.json"
    
    if semester_path.exists() and not force:
        return {
            "success": False,
            "semester": semester,
            "message": f"Data already exists for {semester}. Use force=True to re-scrape.",
            "data_file": str(semester_path)
        }
    
    # Parse semester
    try:
        parts = semester.split("_")
        if len(parts) != 2:
            return {
                "success": False,
                "error": f"Invalid semester format: {semester}",
                "message": "Use format like 'spring_2026' or 'fall_2026'"
            }
        
        season, year = parts[0], parts[1]
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to parse semester identifier"
        }
    
    # Start scraper in background
    scraper_path = Path(__file__).parent / "webscrapper" / "unified_scraper.py"
    
    if not scraper_path.exists():
        return {
            "success": False,
            "error": f"Scraper not found at: {scraper_path}",
            "message": "Web scraper script is missing"
        }
    
    try:
        # Run scraper as background process (non-blocking)
        subprocess.Popen(
            [sys.executable, str(scraper_path), "--semester", season, "--year", year],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from parent process
        )
        
        return {
            "success": True,
            "semester": semester,
            "message": f"Scraper started for {semester}. This will take 5-15 minutes.",
            "note": "This MCP call will timeout, but scraping continues in background.",
            "next_steps": [
                "Wait 5-15 minutes for scraping to complete",
                f"Check for {semester_path.name} file",
                "Retry your original query"
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start scraper"
        }


@mcp.tool()
def check_scraper_status(semester: str = None) -> Dict[str, Any]:
    """
    Check if course data exists for a semester and if scraping is needed.
    
    Args:
        semester: Semester identifier (optional - uses current if not specified)
    
    Returns:
        Status information about data availability
    
    Example:
        check_scraper_status("spring_2026")
    """
    from . import database
    from pathlib import Path
    
    # Determine semester
    if semester is None:
        semester = database.get_selected_semester()
    
    # Check for data files
    data_dir = Path(__file__).parent.parent.parent.parent
    semester_path = data_dir / f"courses_{semester}.json"
    default_path = data_dir / "courses.json"
    
    if semester_path.exists():
        # Check if it has section data
        import json
        with open(semester_path) as f:
            data = json.load(f)
            courses = data.get("courses", data) if isinstance(data, dict) else data
            has_sections = len(courses) > 0 and "sections" in courses[0]
            section_count = len(courses[0].get("sections", [])) if courses else 0
        
        return {
            "data_exists": True,
            "semester": semester,
            "file": str(semester_path),
            "course_count": len(courses),
            "has_sections": has_sections,
            "sample_section_count": section_count,
            "message": "Data exists with sections" if has_sections else "Data exists but missing sections",
            "needs_scraping": not has_sections
        }
    elif default_path.exists():
        return {
            "data_exists": True,
            "semester": semester,
            "file": str(default_path),
            "message": "Using default courses.json (may not have semester-specific data)",
            "needs_scraping": True,
            "recommendation": f"Run scraper to get {semester}-specific data"
        }
    else:
        return {
            "data_exists": False,
            "semester": semester,
            "message": f"No data found for {semester}",
            "needs_scraping": True,
            "recommendation": "Run run_scraper() to fetch data"
        }


@mcp.tool()
def set_semester(semester: str) -> Dict[str, Any]:
    """
    Set the active semester for all subsequent queries.
    
    This semester will be remembered for the rest of the session.
    All course searches, schedule generation, etc. will use this semester.
    
    Args:
        semester: Semester identifier (e.g., "fall_2026", "spring_2027")
    
    Returns:
        Confirmation with semester information
    
    Example:
        set_semester("spring_2027")
    """
    from .tools import courses as course_tools
    from . import database
    
    # Set the semester
    database.set_semester(semester)
    
    # Try to load it (will auto-scrape if needed)
    try:
        database.load_courses(semester)
        
        return {
            "success": True,
            "semester": database.get_current_semester_info(),
            "semester_id": database.get_selected_semester(),
            "course_count": len(database.COURSES),
            "message": f"Active semester set to {database.get_current_semester_info()}"
        }
    except Exception as e:
        return {
            "success": False,
            "semester": semester,
            "error": str(e),
            "message": f"Failed to load semester data: {e}"
        }


@mcp.tool()
def get_current_semester() -> Dict[str, Any]:
    """
    Get information about the currently active semester.
    
    Returns:
        Current semester information
    
    Example:
        get_current_semester()
    """
    from . import database
    
    # Load current semester if not loaded
    if not database.COURSES:
        try:
            database.load_courses()
        except Exception as e:
            return {
                "error": str(e),
                "message": "No semester data loaded"
            }
    
    return {
        "semester": database.get_current_semester_info(),
        "semester_id": database.get_selected_semester(),
        "course_count": len(database.COURSES),
        "message": f"Currently using {database.get_current_semester_info()}"
    }


@mcp.tool()
def search_courses(query: str, semester: str = None) -> Dict[str, Any]:
    """
    Search courses by keyword, department, or course ID.
    
    Args:
        query: Search term (matches course ID, title, or description)
        semester: Semester identifier (optional - uses current if not specified)
    
    Returns:
        Search results with semester context
    
    Example:
        search_courses("computer science")
        search_courses("MATH", semester="spring_2027")
    """
    from . import database
    
    # Use current semester if not specified
    if semester is None:
        semester = database.get_selected_semester()
    
    return course_tools.search_courses_impl(query, semester)


@mcp.tool()
def get_course_info(course_id: str, semester: str = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific course.
    
    Args:
        course_id: Course identifier (e.g., "CS120", "MATH150")
        semester: Semester identifier (optional - uses current if not specified)
    
    Returns:
        Complete course information with semester context
    
    Example:
        get_course_info("acct111")
        get_course_info("cs120", semester="spring_2027")
    """
    from . import database
    
    # Use current semester if not specified
    if semester is None:
        semester = database.get_selected_semester()
    
    return course_tools.get_course_info_impl(course_id, semester)


@mcp.tool()
def get_course_sections(course_id: str, semester: str = None) -> Dict[str, Any]:
    """
    Get all available sections for a course.
    
    Args:
        course_id: Course identifier
        semester: Semester identifier (optional - uses current if not specified)
    
    Returns:
        Dictionary with semester context and list of course sections with meeting times
    
    Example:
        get_course_sections("cs120")
        get_course_sections("math150", semester="spring_2027")
    """
    from . import database
    
    # Use current semester if not specified
    if semester is None:
        semester = database.get_selected_semester()
    
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
) -> Dict[str, Any]:
    """
    Generate all valid schedule combinations from requested courses.
    
    Args:
        requested_courses: List of course IDs to schedule
        max_units: Maximum unit limit (default: 18)
    
    Returns:
        Dictionary with semester context and list of valid schedules with no conflicts
    
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
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))
    
    app = mcp.streamable_http_app()
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

# handles the database for the application, which is a several simple json files

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Use the root directory where courses.json is located
DATA_DIR = Path(__file__).parent.parent.parent.parent

COURSES = []
COURSE_INDEX = {}
CURRENT_SEMESTER = None


def get_default_semester() -> str:
    """
    Get the default semester based on current date.
    
    Returns:
        Semester string like "fall_2026"
    """
    try:
        from . import semesterSync
        return semesterSync.get_default_semester()
    except Exception:
        # Fallback if semesterSync not available
        return "fall_2026"


def load_courses(semester: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load course data from JSON file.
    
    Args:
        semester: Semester identifier (e.g., "fall_2026", "spring_2027")
                 If None, uses current semester based on date
    
    Returns:
        List of course dictionaries
    
    Raises:
        FileNotFoundError: If the course data file doesn't exist
    """
    global COURSES
    global COURSE_INDEX
    global CURRENT_SEMESTER

    # Auto-detect semester if not provided
    if semester is None:
        semester = get_default_semester()
    
    # Try semester-specific file first, fall back to courses.json
    semester_path = DATA_DIR / f"courses_{semester}.json"
    default_path = DATA_DIR / "courses.json"
    
    if semester_path.exists():
        path = semester_path
    elif default_path.exists():
        path = default_path
    else:
        raise FileNotFoundError(
            f"Course data not found for semester: {semester}\n"
            f"Tried: {semester_path} and {default_path}\n"
            f"Run the unified scraper to generate course data:\n"
            f"  python src/canvas_mcp/webscrapper/unified_scraper.py"
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both formats: with metadata wrapper or direct list
    if isinstance(data, dict) and "courses" in data:
        COURSES = data["courses"]
        CURRENT_SEMESTER = data.get("metadata", {}).get("semester", semester)
    else:
        COURSES = data
        CURRENT_SEMESTER = semester

    # Build fast lookup index by course_id
    COURSE_INDEX = {
        course["course_id"].lower(): course
        for course in COURSES
    }

    return COURSES


def get_course_by_id(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a course by its ID (e.g., "CS120", "MATH150").
    
    Args:
        course_id: Course identifier
    
    Returns:
        Course dictionary or None if not found
    """
    if not COURSE_INDEX:
        load_courses()
    
    return COURSE_INDEX.get(course_id.lower())


def search_courses(query: str, department: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search courses by keyword, department, or course ID.
    
    Args:
        query: Search query (matches title, course_id, description)
        department: Optional department filter
    
    Returns:
        List of matching courses
    """
    if not COURSES:
        load_courses()
    
    query_lower = query.lower()
    results = []
    
    for course in COURSES:
        # Check if query matches course_id, title, or description
        matches = (
            query_lower in course["course_id"].lower() or
            query_lower in course["title"].lower() or
            query_lower in course.get("description", "").lower()
        )
        
        # Apply department filter if provided
        if department:
            matches = matches and course.get("department", "").lower() == department.lower()
        
        if matches:
            results.append(course)
    
    return results


def get_all_courses() -> List[Dict[str, Any]]:
    """
    Get all courses in the database.
    
    Returns:
        List of all courses
    """
    if not COURSES:
        load_courses()
    
    return COURSES


def get_current_semester_info() -> Optional[str]:
    """
    Get information about the currently loaded semester.
    
    Returns:
        Semester description string or None
    """
    return CURRENT_SEMESTER


def normalize_course_id(course_id: str) -> str:
    """
    Normalize course ID to lowercase for consistent lookups.
    
    Args:
        course_id: Course identifier
    
    Returns:
        Normalized course ID
    """
    return course_id.lower().strip()


def get_course_sections(course_id: str) -> List[Dict[str, Any]]:
    """
    Get all sections for a course.
    
    Args:
        course_id: Course identifier
    
    Returns:
        List of section dictionaries
    """
    course = get_course_by_id(course_id)
    if not course:
        return []
    
    return course.get("sections", [])

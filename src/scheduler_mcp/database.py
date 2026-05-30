# handles the database for the application, which is a several simple json files


# so db is being stored in a different location? in coding files and not in project files
# also sections are ALL empty in db


import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import subprocess
import sys

# Use the data directory inside scheduler_mcp package
DATA_DIR = Path(__file__).parent / "data"

COURSES = []
COURSE_INDEX = {}
CURRENT_SEMESTER = None
SELECTED_SEMESTER = None  # User's selected semester (persists across calls)


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


def auto_scrape_semester(semester: str) -> bool:
    """
    Automatically run the web scraper to generate semester data.
    
    Args:
        semester: Semester identifier (e.g., "fall_2026")
    
    Returns:
        True if scraping succeeded, False otherwise
    """
    print(f"\n⚠️  Course data not found for {semester}")
    print(f"🔄 Automatically running web scraper...")
    print(f"   (This may take 5-15 minutes)\n")
    
    try:
        # Parse semester string
        parts = semester.split("_")
        if len(parts) != 2:
            print(f"❌ Invalid semester format: {semester}")
            return False
        
        season, year = parts[0], parts[1]
        
        # Run the unified scraper
        scraper_path = Path(__file__).parent / "webscrapper" / "unified_scraper.py"
        
        if not scraper_path.exists():
            print(f"❌ Scraper not found at: {scraper_path}")
            return False
        
        # Run scraper with subprocess
        result = subprocess.run(
            [sys.executable, str(scraper_path), "--semester", season, "--year", year],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully scraped {semester} data!")
            return True
        else:
            print(f"❌ Scraper failed with error:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Scraper timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return False


def set_semester(semester: Optional[str] = None) -> str:
    """
    Set the active semester for the session.
    
    Args:
        semester: Semester identifier (e.g., "fall_2026", "spring_2027")
                 If None, uses current semester based on date
    
    Returns:
        The semester that was set
    """
    global SELECTED_SEMESTER
    
    if semester is None:
        semester = get_default_semester()
    
    SELECTED_SEMESTER = semester
    return semester


def get_selected_semester() -> str:
    """
    Get the currently selected semester.
    
    Returns:
        Semester identifier
    """
    global SELECTED_SEMESTER
    
    if SELECTED_SEMESTER is None:
        SELECTED_SEMESTER = get_default_semester()
    
    return SELECTED_SEMESTER


def load_courses(semester: Optional[str] = None, auto_scrape: bool = True) -> List[Dict[str, Any]]:
    """
    Load course data from JSON file.
    
    Args:
        semester: Semester identifier (e.g., "fall_2026", "spring_2027")
                 If None, uses currently selected semester or auto-detects
        auto_scrape: If True, automatically run scraper if data doesn't exist
                    DEFAULT: False (to avoid MCP timeouts)
    
    Returns:
        List of course dictionaries
    
    Raises:
        FileNotFoundError: If the course data file doesn't exist and auto_scrape is False
    """
    global COURSES
    global COURSE_INDEX
    global CURRENT_SEMESTER
    global SELECTED_SEMESTER

    # Use selected semester if no semester specified
    if semester is None:
        semester = get_selected_semester()
    else:
        # Update selected semester when explicitly provided
        SELECTED_SEMESTER = semester
    
    # Try semester-specific file first, fall back to courses.json
    semester_path = DATA_DIR / f"courses_{semester}.json"
    default_path = DATA_DIR / "courses.json"
    
    # Check if data exists
    if not semester_path.exists() and not default_path.exists():
        if auto_scrape:
            # Try to auto-scrape the data
            if auto_scrape_semester(semester):
                # Retry loading after scraping
                if semester_path.exists():
                    path = semester_path
                elif default_path.exists():
                    path = default_path
                else:
                    raise FileNotFoundError(
                        f"Scraping completed but data file not found: {semester}"
                    )
            else:
                raise FileNotFoundError(
                    f"Course data not found for semester: {semester}\n"
                    f"Tried: {semester_path} and {default_path}\n"
                    f"Auto-scraping failed. Run manually:\n"
                    f"  python src/scheduler_mcp/webscrapper/unified_scraper.py"
                )
        else:
            raise FileNotFoundError(
                f"Course data not found for semester: {semester}\n"
                f"Tried: {semester_path} and {default_path}\n"
                f"\n"
                f"⚠️  Please run the scraper first:\n"
                f"  python src/scheduler_mcp/webscrapper/unified_scraper.py\n"
                f"\n"
                f"This will take 5-15 minutes but only needs to be done once per semester.\n"
                f"After that, all queries will be instant!"
            )
    elif semester_path.exists():
        path = semester_path
    else:
        path = default_path

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both formats: with metadata wrapper or direct list
    if isinstance(data, dict) and "courses" in data:
        COURSES = data["courses"]
        metadata = data.get("metadata", {})
        CURRENT_SEMESTER = metadata.get("semester", semester)
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

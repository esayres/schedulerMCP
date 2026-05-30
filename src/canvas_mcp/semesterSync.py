"""
Semester synchronization and automatic data updates.

This module:
- Detects the current semester based on date
- Coordinates both web scrapers
- Merges course catalog + schedule data
- Updates the local course database
"""

from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

# Semester date ranges (adjust for your school's calendar)
SEMESTER_CALENDAR = {
    "fall": {
        "start_month": 8,   # August
        "start_day": 15,
        "end_month": 12,    # December
        "end_day": 31
    },
    "spring": {
        "start_month": 1,   # January
        "start_day": 1,
        "end_month": 5,     # May
        "end_day": 31
    },
    "summer": {
        "start_month": 6,   # June
        "start_day": 1,
        "end_month": 7,     # July
        "end_day": 31
    }
}

# Term code mapping (adjust for your school's system)
# Format: YYYYTT where TT is term code
# Example: 202630 = Spring 2026 (30 = Spring)
TERM_CODES = {
    "spring": "30",
    "summer": "40", 
    "fall": "10"
}


def get_current_semester() -> Tuple[str, int, str]:
    """
    Determine current semester based on today's date.
    
    Returns:
        Tuple of (season, year, term_code)
        Example: ("spring", 2026, "202630")
    """
    today = date.today()
    month = today.month
    year = today.year
    
    # Determine season
    if SEMESTER_CALENDAR["fall"]["start_month"] <= month <= 12:
        season = "fall"
        academic_year = year
    elif 1 <= month <= SEMESTER_CALENDAR["spring"]["end_month"]:
        season = "spring"
        academic_year = year
    elif SEMESTER_CALENDAR["summer"]["start_month"] <= month <= SEMESTER_CALENDAR["summer"]["end_month"]:
        season = "summer"
        academic_year = year
    else:
        # Default to fall of current year
        season = "fall"
        academic_year = year
    
    # Generate term code
    term_code = f"{academic_year}{TERM_CODES[season]}"
    
    return season, academic_year, term_code


def get_semester_info(season: Optional[str] = None, year: Optional[int] = None) -> Dict[str, str]:
    """
    Get semester information for scraping.
    
    Args:
        season: "fall", "spring", or "summer" (defaults to current)
        year: Academic year (defaults to current)
    
    Returns:
        Dictionary with semester info for both scrapers
    """
    if season is None or year is None:
        season, year, term_code = get_current_semester()
    else:
        term_code = f"{year}{TERM_CODES[season]}"
    
    # Format for catalog scraper (e.g., "2025-26")
    if season == "fall":
        catalog_term = f"{year}-{str(year + 1)[-2:]}"
    else:
        catalog_term = f"{year - 1}-{str(year)[-2:]}"
    
    # Format for schedule scraper (e.g., "202630")
    schedule_term = term_code
    
    # Human-readable description
    term_desc = f"{season.capitalize()} {year}"
    
    return {
        "season": season,
        "year": year,
        "catalog_term": catalog_term,
        "schedule_term": schedule_term,
        "term_code": term_code,
        "term_desc": term_desc,
        "filename": f"courses_{season}_{year}.json"
    }


def merge_course_data(catalog_courses: List[Dict], schedule_sections: List[Dict]) -> List[Dict]:
    """
    Merge course catalog data with schedule/section data.
    
    Args:
        catalog_courses: List of courses from allCoursesScrapper
        schedule_sections: List of sections from schuedulerScrapper
    
    Returns:
        List of courses with embedded section data
    """
    # Build index of sections by course ID
    sections_by_course = {}
    
    for section in schedule_sections:
        course_name = section.get("course", "")
        
        # Extract course code from formats like:
        # "PHYS 211 - General Physics" -> "phys211"
        # "ACCT 111" -> "acct111"
        if " - " in course_name:
            # Split on " - " and take the first part
            course_code = course_name.split(" - ")[0].strip()
        else:
            course_code = course_name
        
        # Normalize: remove spaces and lowercase (e.g., "PHYS 211" -> "phys211")
        course_id = course_code.replace(" ", "").lower()
        
        if course_id not in sections_by_course:
            sections_by_course[course_id] = []
        
        # Create section entry with all fields
        section_entry = {
            "crn": section.get("crn"),
            "section": section.get("section"),
            "credits": section.get("credits"),
            "days": section.get("days", []),
            "time": section.get("time"),
            "location": section.get("location"),
            "instructor": section.get("instructor"),
            "status": section.get("status", "Open")
        }
        
        # Add additional_times if present (for lab times)
        if "additional_times" in section:
            section_entry["additional_times"] = section["additional_times"]
        
        sections_by_course[course_id].append(section_entry)
    
    # Merge sections into courses
    merged_courses = []
    courses_with_sections = 0
    total_sections_added = 0
    
    for course in catalog_courses:
        course_id = course.get("course_id", "").lower()
        
        # Add sections if available
        if course_id in sections_by_course:
            course["sections"] = sections_by_course[course_id]
            courses_with_sections += 1
            total_sections_added += len(sections_by_course[course_id])
        else:
            course["sections"] = []
        
        merged_courses.append(course)
    
    # Print merge statistics
    print(f"\nMerge Statistics:")
    print(f"  • Total catalog courses: {len(catalog_courses)}")
    print(f"  • Total schedule sections: {len(schedule_sections)}")
    print(f"  • Unique courses with sections: {len(sections_by_course)}")
    print(f"  • Courses matched with sections: {courses_with_sections}")
    print(f"  • Total sections added: {total_sections_added}")
    
    # Show some unmatched courses for debugging
    unmatched_schedule = set(sections_by_course.keys())
    catalog_ids = {c.get("course_id", "").lower() for c in catalog_courses}
    unmatched_in_schedule = unmatched_schedule - catalog_ids
    
    if unmatched_in_schedule:
        print(f"  • Sections without catalog match: {len(unmatched_in_schedule)}")
        print(f"    Examples: {list(unmatched_in_schedule)[:5]}")
    
    return merged_courses


def save_course_database(courses: List[Dict], semester_info: Dict, output_dir: Path = None) -> Path:
    """
    Save course database to JSON file.
    
    Args:
        courses: List of course dictionaries
        semester_info: Semester information
        output_dir: Output directory (defaults to src/canvas_mcp/data/)
    
    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "data"
    
    # Save with semester-specific filename
    filename = semester_info["filename"]
    filepath = output_dir / filename
    
    # Also save as default courses.json
    default_filepath = output_dir / "courses.json"
    
    # Add metadata
    data = {
        "metadata": {
            "semester": semester_info["term_desc"],
            "season": semester_info["season"],
            "year": semester_info["year"],
            "term_code": semester_info["term_code"],
            "generated_at": datetime.now().isoformat(),
            "course_count": len(courses)
        },
        "courses": courses
    }
    
    # Save semester-specific file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    # Save as default
    with open(default_filepath, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2)
    
    print(f"✓ Saved {len(courses)} courses to {filepath}")
    print(f"✓ Saved default to {default_filepath}")
    
    return filepath


def check_database_freshness(semester_info: Dict, output_dir: Path = None) -> bool:
    """
    Check if database exists and is current.
    
    Args:
        semester_info: Semester information
        output_dir: Output directory (defaults to src/canvas_mcp/data/)
    
    Returns:
        True if database is fresh, False if needs update
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "data"
    
    filepath = output_dir / semester_info["filename"]
    
    if not filepath.exists():
        return False
    
    # Check if file is from current semester
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        metadata = data.get("metadata", {})
        file_term = metadata.get("term_code")
        
        return file_term == semester_info["term_code"]
    except Exception:
        return False


def get_available_semesters(output_dir: Path = None) -> List[Dict]:
    """
    Get list of available semester databases.
    
    Args:
        output_dir: Output directory (defaults to src/canvas_mcp/data/)
    
    Returns:
        List of semester info dictionaries
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "data"
    
    semesters = []
    
    # Look for courses_<season>_<year>.json files
    for filepath in output_dir.glob("courses_*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            
            semesters.append({
                "filename": filepath.name,
                "semester": metadata.get("semester"),
                "season": metadata.get("season"),
                "year": metadata.get("year"),
                "term_code": metadata.get("term_code"),
                "course_count": metadata.get("course_count"),
                "generated_at": metadata.get("generated_at")
            })
        except Exception:
            continue
    
    return sorted(semesters, key=lambda x: x.get("term_code", ""), reverse=True)


# Convenience function for database module
def get_default_semester() -> str:
    """
    Get default semester identifier for database loading.
    
    Returns:
        Semester string like "fall_2026"
    """
    season, year, _ = get_current_semester()
    return f"{season}_{year}"

"""
Scheduling logic and algorithms for course schedule generation.

This module handles:
- Schedule conflict detection
- Schedule generation and combination
- Schedule scoring and ranking
- Prerequisite and corequisite validation
"""

from typing import List, Dict, Any, Tuple, Optional
from itertools import product
from datetime import datetime, time
from . import database


def parse_time(time_str: str) -> Optional[time]:
    """
    Parse time string to time object.
    
    Args:
        time_str: Time string (e.g., "10:00 AM", "14:30")
    
    Returns:
        time object or None if parsing fails
    """
    if not time_str:
        return None
    
    try:
        # Try parsing with AM/PM
        return datetime.strptime(time_str.strip(), "%I:%M %p").time()
    except ValueError:
        try:
            # Try 24-hour format
            return datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError:
            return None


def times_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    """
    Check if two time ranges overlap.
    
    Args:
        start1, end1: First time range
        start2, end2: Second time range
    
    Returns:
        True if times overlap
    """
    return start1 < end2 and start2 < end1


def detect_conflicts(course_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Detect time conflicts between courses.
    
    Note: This is a simplified version since the current courses.json
    doesn't include section/meeting time data. This would need to be
    enhanced when section data is available.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        List of conflict dictionaries
    """
    conflicts = []
    
    # TODO: Implement actual conflict detection when section data is available
    # For now, return empty list as placeholder
    
    return conflicts


def validate_prerequisites(
    completed_courses: List[str],
    requested_courses: List[str]
) -> Dict[str, Any]:
    """
    Validate that prerequisites are satisfied for requested courses.
    
    Args:
        completed_courses: List of completed course IDs
        requested_courses: List of requested course IDs
    
    Returns:
        Validation result with satisfied/unsatisfied prerequisites
    """
    completed_set = {database.normalize_course_id(c) for c in completed_courses}
    missing_prereqs = []
    
    for course_id in requested_courses:
        course = database.get_course_by_id(course_id)
        if not course:
            missing_prereqs.append({
                "course": course_id,
                "error": "Course not found"
            })
            continue
        
        prereqs = course.get("prereqs", [])
        if not prereqs:
            continue
        
        # Check if any prerequisite is satisfied
        # Note: Current data has OR logic (any prereq satisfies)
        prereq_satisfied = any(
            database.normalize_course_id(p) in completed_set
            for p in prereqs
        )
        
        if not prereq_satisfied and prereqs:
            missing_prereqs.append({
                "course": course_id,
                "missing_prerequisites": prereqs,
                "message": f"Missing prerequisite for {course_id}: need one of {prereqs}"
            })
    
    return {
        "valid": len(missing_prereqs) == 0,
        "missing_prerequisites": missing_prereqs,
        "message": "All prerequisites satisfied" if not missing_prereqs else "Some prerequisites not satisfied"
    }


def validate_corequisites(requested_courses: List[str]) -> Dict[str, Any]:
    """
    Validate that corequisites are included in requested courses.
    
    Args:
        requested_courses: List of requested course IDs
    
    Returns:
        Validation result with satisfied/unsatisfied corequisites
    """
    requested_set = {database.normalize_course_id(c) for c in requested_courses}
    missing_coreqs = []
    
    for course_id in requested_courses:
        course = database.get_course_by_id(course_id)
        if not course:
            continue
        
        coreqs = course.get("coreqs", [])
        for coreq in coreqs:
            if database.normalize_course_id(coreq) not in requested_set:
                missing_coreqs.append({
                    "course": course_id,
                    "missing_corequisite": coreq,
                    "message": f"{course_id} requires {coreq} as corequisite"
                })
    
    return {
        "valid": len(missing_coreqs) == 0,
        "missing_corequisites": missing_coreqs,
        "message": "All corequisites satisfied" if not missing_coreqs else "Some corequisites not satisfied"
    }


def calculate_total_units(course_ids: List[str]) -> float:
    """
    Calculate total units for a list of courses.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Total units
    """
    total = 0.0
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if course:
            try:
                total += float(course.get("min_units", 0))
            except (ValueError, TypeError):
                pass
    return total


def score_schedule(course_ids: List[str], preference: str = "balanced") -> float:
    """
    Score a schedule based on preference criteria.
    
    Args:
        course_ids: List of course IDs in schedule
        preference: Scoring preference ("no_mornings", "compact", "balanced")
    
    Returns:
        Schedule score (higher is better)
    """
    score = 100.0
    
    # Base score on number of courses (prefer fuller schedules)
    score += len(course_ids) * 5
    
    # TODO: Implement actual scoring when section/time data is available
    # For now, return base score
    
    if preference == "balanced":
        # Prefer moderate course loads
        if 3 <= len(course_ids) <= 5:
            score += 20
    elif preference == "compact":
        # Prefer more courses (denser schedule)
        score += len(course_ids) * 10
    elif preference == "no_mornings":
        # Would penalize morning classes when time data available
        pass
    
    return score


def generate_schedules(
    course_ids: List[str],
    max_units: int = 18,
    max_schedules: int = 100
) -> List[Dict[str, Any]]:
    """
    Generate valid schedule combinations.
    
    Note: Simplified version without section data.
    When section data is available, this will generate all
    valid section combinations.
    
    Args:
        course_ids: List of course IDs to schedule
        max_units: Maximum unit limit
        max_schedules: Maximum number of schedules to return
    
    Returns:
        List of valid schedules
    """
    schedules = []
    
    # Calculate total units
    total_units = calculate_total_units(course_ids)
    
    if total_units > max_units:
        return []
    
    # For now, create a single schedule with all courses
    # TODO: Generate combinations when section data is available
    schedule = {
        "courses": course_ids,
        "total_units": total_units,
        "conflicts": [],
        "valid": True
    }
    
    schedules.append(schedule)
    
    return schedules[:max_schedules]


def validate_course_plan(course_plan: List[List[str]]) -> Dict[str, Any]:
    """
    Validate a multi-semester course plan.
    
    Args:
        course_plan: List of semesters, each containing course IDs
    
    Returns:
        Validation result
    """
    completed = []
    errors = []
    
    for semester_idx, semester_courses in enumerate(course_plan):
        # Validate prerequisites for this semester
        prereq_result = validate_prerequisites(completed, semester_courses)
        
        if not prereq_result["valid"]:
            for missing in prereq_result["missing_prerequisites"]:
                errors.append({
                    "semester": semester_idx + 1,
                    "course": missing["course"],
                    "issue": missing.get("message", "Missing prerequisite")
                })
        
        # Validate corequisites within semester
        coreq_result = validate_corequisites(semester_courses)
        
        if not coreq_result["valid"]:
            for missing in coreq_result["missing_corequisites"]:
                errors.append({
                    "semester": semester_idx + 1,
                    "course": missing["course"],
                    "issue": missing.get("message", "Missing corequisite")
                })
        
        # Add this semester's courses to completed
        completed.extend(semester_courses)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "message": "Course plan is valid" if not errors else f"Found {len(errors)} issue(s) in course plan"
    }
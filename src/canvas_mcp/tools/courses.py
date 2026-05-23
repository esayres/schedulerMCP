"""
MCP-exposed course planning and scheduling tools.

These are the functions that AI assistants can call via the MCP protocol.
Tool functions stay thin and delegate to core logic modules.
"""

from typing import List, Dict, Any
from .. import database, schueduling, workload


def search_courses_impl(query: str, semester: str = "fall_2026") -> List[Dict[str, Any]]:
    """
    Search courses by keyword, department, or course ID.
    
    Args:
        query: Search query
        semester: Semester identifier
    
    Returns:
        List of matching courses
    """
    try:
        database.load_courses(semester)
    except FileNotFoundError:
        return []
    
    results = database.search_courses(query)
    
    # Return simplified course info
    return [
        {
            "course_id": c["course_id"],
            "title": c["title"],
            "units": c.get("min_units", ""),
            "department": c.get("department", ""),
            "description": c.get("description", "")[:200] + "..." if len(c.get("description", "")) > 200 else c.get("description", "")
        }
        for c in results
    ]


def get_course_info_impl(course_id: str, semester: str = "fall_2026") -> Dict[str, Any]:
    """
    Get detailed course information.
    
    Args:
        course_id: Course identifier
        semester: Semester identifier
    
    Returns:
        Course details or error
    """
    try:
        database.load_courses(semester)
    except FileNotFoundError:
        return {"error": f"Course data not found for semester: {semester}"}
    
    course = database.get_course_by_id(course_id)
    
    if not course:
        return {"error": f"Course not found: {course_id}"}
    
    return {
        "course_id": course["course_id"],
        "title": course["title"],
        "description": course.get("description", ""),
        "units": course.get("min_units", ""),
        "prerequisites": course.get("prereqs", []),
        "corequisites": course.get("coreqs", []),
        "advisory": course.get("advisory", []),
        "lecture_hours": course.get("lecture_hours", "0"),
        "lab_hours": course.get("lab_hours", "0"),
        "contact_hours": course.get("contact_hours", "0"),
        "out_of_class_hours": course.get("out_of_class_hours", "0"),
        "department": course.get("department", "")
    }


def get_course_sections_impl(course_id: str, semester: str = "fall_2026") -> List[Dict[str, Any]]:
    """
    Get all sections for a course.
    
    Note: Current data doesn't include section information.
    This is a placeholder for when section data is available.
    
    Args:
        course_id: Course identifier
        semester: Semester identifier
    
    Returns:
        List of sections (currently empty)
    """
    try:
        database.load_courses(semester)
    except FileNotFoundError:
        return []
    
    course = database.get_course_by_id(course_id)
    
    if not course:
        return []
    
    # TODO: Return actual sections when data is available
    return []


def detect_schedule_conflicts_impl(course_ids: List[str]) -> Dict[str, Any]:
    """
    Detect time conflicts between courses.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Conflict detection results
    """
    database.load_courses()
    
    conflicts = schueduling.detect_conflicts(course_ids)
    
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
        "message": "No conflicts detected" if not conflicts else f"Found {len(conflicts)} conflict(s)"
    }


def generate_possible_schedules_impl(
    requested_courses: List[str],
    max_units: int = 18
) -> List[Dict[str, Any]]:
    """
    Generate valid schedule combinations.
    
    Args:
        requested_courses: List of course IDs
        max_units: Maximum unit limit
    
    Returns:
        List of valid schedules
    """
    database.load_courses()
    
    schedules = schueduling.generate_schedules(requested_courses, max_units)
    
    if not schedules:
        return []
    
    return schedules


def suggest_best_schedule_impl(
    requested_courses: List[str],
    preference: str = "balanced",
    max_units: int = 18
) -> Dict[str, Any]:
    """
    Suggest the best schedule based on preferences.
    
    Args:
        requested_courses: List of course IDs
        preference: Preference type ("balanced", "compact", "no_mornings")
        max_units: Maximum unit limit
    
    Returns:
        Best schedule recommendation
    """
    database.load_courses()
    
    schedules = schueduling.generate_schedules(requested_courses, max_units)
    
    if not schedules:
        total_units = schueduling.calculate_total_units(requested_courses)
        if total_units > max_units:
            return {
                "error": f"Total units ({total_units}) exceeds maximum ({max_units})",
                "suggestion": "Consider removing some courses or increasing unit limit"
            }
        return {
            "error": "No valid schedules found",
            "suggestion": "Check for conflicts or unavailable courses"
        }
    
    # Score and sort schedules
    scored_schedules = []
    for schedule in schedules:
        score = schueduling.score_schedule(schedule["courses"], preference)
        scored_schedules.append({
            **schedule,
            "score": score
        })
    
    scored_schedules.sort(key=lambda x: x["score"], reverse=True)
    best = scored_schedules[0]
    
    return {
        "schedule": best,
        "preference": preference,
        "message": f"Best schedule found with score {best['score']}"
    }


def validate_prerequisites_impl(
    completed_courses: List[str],
    requested_courses: List[str]
) -> Dict[str, Any]:
    """
    Validate prerequisites for requested courses.
    
    Args:
        completed_courses: List of completed course IDs
        requested_courses: List of requested course IDs
    
    Returns:
        Validation results
    """
    database.load_courses()
    
    prereq_result = schueduling.validate_prerequisites(completed_courses, requested_courses)
    coreq_result = schueduling.validate_corequisites(requested_courses)
    
    return {
        "prerequisites_valid": prereq_result["valid"],
        "corequisites_valid": coreq_result["valid"],
        "overall_valid": prereq_result["valid"] and coreq_result["valid"],
        "prerequisite_issues": prereq_result.get("missing_prerequisites", []),
        "corequisite_issues": coreq_result.get("missing_corequisites", []),
        "message": "All requirements satisfied" if (prereq_result["valid"] and coreq_result["valid"]) else "Some requirements not satisfied"
    }


def validate_course_plan_impl(course_plan: List[List[str]]) -> Dict[str, Any]:
    """
    Validate a multi-semester course plan.
    
    Args:
        course_plan: List of semesters, each containing course IDs
    
    Returns:
        Validation results
    """
    database.load_courses()
    
    result = schueduling.validate_course_plan(course_plan)
    
    return result


def estimate_semester_workload_impl(course_ids: List[str]) -> Dict[str, Any]:
    """
    Estimate weekly workload for courses.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Workload estimation
    """
    database.load_courses()
    
    workload_result = workload.estimate_workload(course_ids)
    heavy_check = workload.detect_heavy_semester(course_ids)
    
    return {
        **workload_result,
        "is_heavy_semester": heavy_check["is_heavy"],
        "warnings": heavy_check.get("warnings", [])
    }


def detect_deadline_clusters_impl(course_ids: List[str]) -> Dict[str, Any]:
    """
    Predict weeks with heavy workload overlap.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Deadline cluster predictions
    """
    database.load_courses()
    
    return workload.detect_deadline_clusters(course_ids)
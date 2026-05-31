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
    
    Checks for overlapping meeting times between courses, including
    lecture times and additional times (labs).
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        List of conflict dictionaries with details about overlaps
    """
    conflicts = []
    
    # Get courses with sections
    courses = []
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if course and course.get("sections"):
            courses.append(course)
    
    # Check each pair of courses
    for i in range(len(courses)):
        for j in range(i + 1, len(courses)):
            course1 = courses[i]
            course2 = courses[j]
            
            # Check all section combinations
            for section1 in course1.get("sections", []):
                for section2 in course2.get("sections", []):
                    conflict = check_section_conflict(
                        course1["course_id"], section1,
                        course2["course_id"], section2
                    )
                    if conflict:
                        conflicts.append(conflict)
    
    return conflicts


def check_section_conflict(
    course1_id: str, section1: Dict[str, Any],
    course2_id: str, section2: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Check if two course sections have time conflicts.
    
    Args:
        course1_id: First course ID
        section1: First course section data
        course2_id: Second course ID
        section2: Second course section data
    
    Returns:
        Conflict dictionary if conflict exists, None otherwise
    """
    # Check main meeting times
    conflict = check_time_conflict(
        section1.get("days", []), section1.get("time", ""),
        section2.get("days", []), section2.get("time", "")
    )
    
    if conflict:
        return {
            "course1": course1_id,
            "course2": course2_id,
            "section1": section1.get("crn", ""),
            "section2": section2.get("crn", ""),
            "conflict_type": "lecture",
            "days": conflict["days"],
            "time1": section1.get("time", ""),
            "time2": section2.get("time", ""),
            "message": f"{course1_id} and {course2_id} conflict on {', '.join(conflict['days'])}"
        }
    
    # Check additional times (labs) for section1
    for add_time1 in section1.get("additional_times", []):
        conflict = check_time_conflict(
            add_time1.get("days", []), add_time1.get("time", ""),
            section2.get("days", []), section2.get("time", "")
        )
        if conflict:
            return {
                "course1": course1_id,
                "course2": course2_id,
                "section1": section1.get("crn", ""),
                "section2": section2.get("crn", ""),
                "conflict_type": "lab_lecture",
                "days": conflict["days"],
                "time1": add_time1.get("time", ""),
                "time2": section2.get("time", ""),
                "message": f"{course1_id} lab and {course2_id} lecture conflict on {', '.join(conflict['days'])}"
            }
    
    # Check additional times (labs) for section2
    for add_time2 in section2.get("additional_times", []):
        conflict = check_time_conflict(
            section1.get("days", []), section1.get("time", ""),
            add_time2.get("days", []), add_time2.get("time", "")
        )
        if conflict:
            return {
                "course1": course1_id,
                "course2": course2_id,
                "section1": section1.get("crn", ""),
                "section2": section2.get("crn", ""),
                "conflict_type": "lecture_lab",
                "days": conflict["days"],
                "time1": section1.get("time", ""),
                "time2": add_time2.get("time", ""),
                "message": f"{course1_id} lecture and {course2_id} lab conflict on {', '.join(conflict['days'])}"
            }
    
    # Check lab vs lab
    for add_time1 in section1.get("additional_times", []):
        for add_time2 in section2.get("additional_times", []):
            conflict = check_time_conflict(
                add_time1.get("days", []), add_time1.get("time", ""),
                add_time2.get("days", []), add_time2.get("time", "")
            )
            if conflict:
                return {
                    "course1": course1_id,
                    "course2": course2_id,
                    "section1": section1.get("crn", ""),
                    "section2": section2.get("crn", ""),
                    "conflict_type": "lab_lab",
                    "days": conflict["days"],
                    "time1": add_time1.get("time", ""),
                    "time2": add_time2.get("time", ""),
                    "message": f"{course1_id} lab and {course2_id} lab conflict on {', '.join(conflict['days'])}"
                }
    
    return None


def check_time_conflict(
    days1: List[str], time1: str,
    days2: List[str], time2: str
) -> Optional[Dict[str, Any]]:
    """
    Check if two meeting times conflict.
    
    Args:
        days1: Days for first meeting (e.g., ["M", "W"])
        time1: Time for first meeting (e.g., "10:00am - 11:50am")
        days2: Days for second meeting
        time2: Time for second meeting
    
    Returns:
        Conflict info if times overlap, None otherwise
    """
    # Check if days overlap
    overlapping_days = set(days1) & set(days2)
    if not overlapping_days:
        return None
    
    # Parse times
    if not time1 or not time2:
        return None
    
    try:
        # Parse time ranges (e.g., "10:00am - 11:50am")
        if " - " in time1 and " - " in time2:
            start1_str, end1_str = time1.split(" - ")
            start2_str, end2_str = time2.split(" - ")
            
            start1 = parse_time(start1_str)
            end1 = parse_time(end1_str)
            start2 = parse_time(start2_str)
            end2 = parse_time(end2_str)
            
            if all([start1, end1, start2, end2]):
                if times_overlap(start1, end1, start2, end2):
                    return {
                        "days": list(overlapping_days),
                        "overlap": True
                    }
    except Exception:
        pass
    
    return None


def validate_prerequisites(
    completed_courses: List[str],
    requested_courses: List[str]
) -> Dict[str, Any]:
    """
    Validate that prerequisites are satisfied for requested courses.
    
    Prerequisite Logic:
    - Flat items in array: ALL required (AND logic)
    - Nested arrays: ONE of the items required (OR logic)
    
    Example: ["MATH150", ["MATH140", "MATH140H"], "CS130"]
    Means: MATH150 AND (MATH140 OR MATH140H) AND CS130
    
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
        
        # Check each prerequisite requirement
        unsatisfied_requirements = []
        
        for prereq in prereqs:
            if isinstance(prereq, list):
                # Nested array: ONE of these courses is required (OR logic)
                if not any(database.normalize_course_id(p) in completed_set for p in prereq):
                    unsatisfied_requirements.append({
                        "type": "one_of",
                        "options": prereq,
                        "message": f"Need one of: {', '.join(prereq)}"
                    })
            else:
                # Single course: THIS course is required (AND logic)
                if database.normalize_course_id(prereq) not in completed_set:
                    unsatisfied_requirements.append({
                        "type": "required",
                        "course": prereq,
                        "message": f"Need: {prereq}"
                    })
        
        if unsatisfied_requirements:
            missing_prereqs.append({
                "course": course_id,
                "missing_prerequisites": unsatisfied_requirements,
                "message": f"Missing prerequisites for {course_id}"
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


def score_schedule(schedule: Dict[str, Any], preference: str = "balanced") -> float:
    """
    Score a schedule based on preference criteria using actual meeting times.
    
    Args:
        schedule: Schedule dictionary with courses and sections
        preference: Scoring preference ("no_mornings", "compact", "balanced")
    
    Returns:
        Schedule score (higher is better)
    """
    score = 100.0
    
    # Base score on number of courses (prefer fuller schedules)
    course_ids = schedule.get("courses", [])
    score += len(course_ids) * 5
    
    # Get all meeting times from the schedule
    morning_classes = 0
    total_classes = 0
    days_used = set()
    all_times = []
    
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if not course or not course.get("sections"):
            continue
        
        # Find the section used in this schedule (use first section for now)
        section = course["sections"][0]
        
        # Check main meeting time
        if section.get("time") and section.get("days"):
            total_classes += 1
            days_used.update(section["days"])
            
            # Parse time to check if it's a morning class
            time_str = section["time"]
            if " - " in time_str:
                start_str = time_str.split(" - ")[0]
                start_time = parse_time(start_str)
                
                if start_time:
                    all_times.append((section["days"], start_time))
                    # Morning is before 10:00 AM
                    if start_time < time(10, 0):
                        morning_classes += 1
        
        # Check additional times (labs)
        for add_time in section.get("additional_times", []):
            if add_time.get("time") and add_time.get("days"):
                total_classes += 1
                days_used.update(add_time["days"])
                
                time_str = add_time["time"]
                if " - " in time_str:
                    start_str = time_str.split(" - ")[0]
                    start_time = parse_time(start_str)
                    
                    if start_time:
                        all_times.append((add_time["days"], start_time))
                        if start_time < time(10, 0):
                            morning_classes += 1
    
    # Apply preference-based scoring
    if preference == "no_mornings":
        # Penalize morning classes heavily
        score -= morning_classes * 15
        # Bonus for no morning classes
        if morning_classes == 0:
            score += 30
    
    elif preference == "compact":
        # Prefer fewer days on campus
        score -= len(days_used) * 5
        # Bonus for concentrated schedule (3 days or less)
        if len(days_used) <= 3:
            score += 25
    
    elif preference == "balanced":
        # Prefer moderate number of days (3-4 days)
        if 3 <= len(days_used) <= 4:
            score += 20
        # Slight penalty for too many morning classes
        if total_classes > 0:
            morning_ratio = morning_classes / total_classes
            if morning_ratio > 0.5:
                score -= 10
    
    return score


def generate_schedules(
    course_ids: List[str],
    max_units: int = 18,
    max_schedules: int = 100,
    preference: str = "balanced"
) -> List[Dict[str, Any]]:
    """
    Generate valid schedule combinations from all section possibilities.
    
    Creates all possible combinations of course sections, checks for conflicts,
    validates unit limits, and scores each valid schedule.
    
    Args:
        course_ids: List of course IDs to schedule
        max_units: Maximum unit limit
        max_schedules: Maximum number of schedules to return
        preference: Scoring preference for ranking schedules
    
    Returns:
        List of valid schedules, sorted by score (best first)
    """
    # Calculate total units
    total_units = calculate_total_units(course_ids)
    
    if total_units > max_units:
        return []
    
    # Get courses with their sections
    courses_with_sections = []
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if not course:
            continue
        
        sections = course.get("sections", [])
        if not sections:
            # Course has no sections, can't schedule
            continue
        
        courses_with_sections.append({
            "course_id": course_id,
            "sections": sections,
            "course": course
        })
    
    # If any course has no sections, can't create valid schedules
    if len(courses_with_sections) != len(course_ids):
        return []
    
    # Generate all section combinations using itertools.product
    section_lists = [c["sections"] for c in courses_with_sections]
    all_combinations = product(*section_lists)
    
    valid_schedules = []
    
    for combination in all_combinations:
        # Build schedule from this combination
        schedule_courses = []
        schedule_sections = []
        
        for i, section in enumerate(combination):
            course_id = courses_with_sections[i]["course_id"]
            schedule_courses.append(course_id)
            schedule_sections.append({
                "course_id": course_id,
                "crn": section.get("crn", ""),
                "section": section.get("section", ""),
                "days": section.get("days", []),
                "time": section.get("time", ""),
                "location": section.get("location", ""),
                "instructor": section.get("instructor", ""),
                "additional_times": section.get("additional_times", [])
            })
        
        # Check for conflicts in this combination
        conflicts = check_combination_conflicts(schedule_sections)
        
        # Create schedule object
        schedule = {
            "courses": schedule_courses,
            "sections": schedule_sections,
            "total_units": total_units,
            "conflicts": conflicts,
            "valid": len(conflicts) == 0
        }
        
        # Only keep valid schedules
        if schedule["valid"]:
            # Score the schedule
            schedule["score"] = score_schedule(schedule, preference)
            valid_schedules.append(schedule)
            
            # Stop if we have enough schedules
            if len(valid_schedules) >= max_schedules:
                break
    
    # Sort by score (highest first)
    valid_schedules.sort(key=lambda s: s["score"], reverse=True)
    
    return valid_schedules[:max_schedules]


def check_combination_conflicts(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check for time conflicts within a specific section combination.
    
    Args:
        sections: List of section dictionaries with course_id and time info
    
    Returns:
        List of conflicts found
    """
    conflicts = []
    
    # Check each pair of sections
    for i in range(len(sections)):
        for j in range(i + 1, len(sections)):
            section1 = sections[i]
            section2 = sections[j]
            
            # Check main meeting times
            conflict = check_time_conflict(
                section1.get("days", []), section1.get("time", ""),
                section2.get("days", []), section2.get("time", "")
            )
            
            if conflict:
                conflicts.append({
                    "course1": section1["course_id"],
                    "course2": section2["course_id"],
                    "section1": section1.get("crn", ""),
                    "section2": section2.get("crn", ""),
                    "conflict_type": "lecture",
                    "days": conflict["days"],
                    "time1": section1.get("time", ""),
                    "time2": section2.get("time", "")
                })
            
            # Check additional times (labs) for section1
            for add_time1 in section1.get("additional_times", []):
                conflict = check_time_conflict(
                    add_time1.get("days", []), add_time1.get("time", ""),
                    section2.get("days", []), section2.get("time", "")
                )
                if conflict:
                    conflicts.append({
                        "course1": section1["course_id"],
                        "course2": section2["course_id"],
                        "section1": section1.get("crn", ""),
                        "section2": section2.get("crn", ""),
                        "conflict_type": "lab_lecture",
                        "days": conflict["days"],
                        "time1": add_time1.get("time", ""),
                        "time2": section2.get("time", "")
                    })
            
            # Check additional times (labs) for section2
            for add_time2 in section2.get("additional_times", []):
                conflict = check_time_conflict(
                    section1.get("days", []), section1.get("time", ""),
                    add_time2.get("days", []), add_time2.get("time", "")
                )
                if conflict:
                    conflicts.append({
                        "course1": section1["course_id"],
                        "course2": section2["course_id"],
                        "section1": section1.get("crn", ""),
                        "section2": section2.get("crn", ""),
                        "conflict_type": "lecture_lab",
                        "days": conflict["days"],
                        "time1": section1.get("time", ""),
                        "time2": add_time2.get("time", "")
                    })
            
            # Check lab vs lab
            for add_time1 in section1.get("additional_times", []):
                for add_time2 in section2.get("additional_times", []):
                    conflict = check_time_conflict(
                        add_time1.get("days", []), add_time1.get("time", ""),
                        add_time2.get("days", []), add_time2.get("time", "")
                    )
                    if conflict:
                        conflicts.append({
                            "course1": section1["course_id"],
                            "course2": section2["course_id"],
                            "section1": section1.get("crn", ""),
                            "section2": section2.get("crn", ""),
                            "conflict_type": "lab_lab",
                            "days": conflict["days"],
                            "time1": add_time1.get("time", ""),
                            "time2": add_time2.get("time", "")
                        })
    
    return conflicts


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
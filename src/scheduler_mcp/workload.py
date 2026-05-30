"""
Workload estimation and analysis.

This module handles:
- Weekly workload calculation
- Difficulty scoring
- Lab-heavy schedule detection
- Deadline cluster prediction
- Balanced schedule scoring
"""

from typing import List, Dict, Any
from . import database


def estimate_workload(course_ids: List[str]) -> Dict[str, Any]:
    """
    Estimate weekly workload for a list of courses.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Workload breakdown with hours and assessment
    """
    total_contact_hours = 0.0
    total_out_of_class_hours = 0.0
    total_lecture_hours = 0.0
    total_lab_hours = 0.0
    course_breakdown = []
    
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if not course:
            continue
        
        try:
            contact_hours = float(course.get("contact_hours", 0))
            out_of_class_hours = float(course.get("out_of_class_hours", 0))
            lecture_hours = float(course.get("lecture_hours", 0))
            lab_hours = float(course.get("lab_hours", 0))
            
            # Convert semester hours to weekly hours (assuming 18-week semester)
            weekly_contact = contact_hours / 18
            weekly_out_of_class = out_of_class_hours / 18
            weekly_lecture = lecture_hours / 18
            weekly_lab = lab_hours / 18
            
            total_contact_hours += weekly_contact
            total_out_of_class_hours += weekly_out_of_class
            total_lecture_hours += weekly_lecture
            total_lab_hours += weekly_lab
            
            course_breakdown.append({
                "course_id": course_id,
                "title": course.get("title", ""),
                "weekly_contact_hours": round(weekly_contact, 1),
                "weekly_out_of_class_hours": round(weekly_out_of_class, 1),
                "weekly_total_hours": round(weekly_contact + weekly_out_of_class, 1)
            })
        except (ValueError, TypeError):
            continue
    
    total_weekly_hours = total_contact_hours + total_out_of_class_hours
    
    # Assess workload level
    if total_weekly_hours < 20:
        assessment = "light"
    elif total_weekly_hours < 35:
        assessment = "moderate"
    elif total_weekly_hours < 50:
        assessment = "heavy"
    else:
        assessment = "very heavy"
    
    return {
        "total_contact_hours": round(total_contact_hours, 1),
        "total_out_of_class_hours": round(total_out_of_class_hours, 1),
        "total_weekly_hours": round(total_weekly_hours, 1),
        "total_lecture_hours": round(total_lecture_hours, 1),
        "total_lab_hours": round(total_lab_hours, 1),
        "assessment": assessment,
        "course_breakdown": course_breakdown
    }


def calculate_difficulty_score(course_id: str) -> float:
    """
    Calculate difficulty score for a course based on workload.
    
    Args:
        course_id: Course ID
    
    Returns:
        Difficulty score (0-10, higher is more difficult)
    """
    course = database.get_course_by_id(course_id)
    if not course:
        return 5.0  # Default medium difficulty
    
    try:
        units = float(course.get("min_units", 3))
        lab_hours = float(course.get("lab_hours", 0))
        out_of_class = float(course.get("out_of_class_hours", 0))
        
        # Base difficulty on units
        difficulty = units * 1.5
        
        # Add difficulty for lab courses
        if lab_hours > 0:
            difficulty += 1.5
        
        # Add difficulty for high out-of-class hours
        weekly_out_of_class = out_of_class / 18
        if weekly_out_of_class > 8:
            difficulty += 1.0
        
        return min(difficulty, 10.0)
    except (ValueError, TypeError):
        return 5.0


def detect_heavy_semester(course_ids: List[str]) -> Dict[str, Any]:
    """
    Detect if a semester schedule is too heavy.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Analysis of semester difficulty
    """
    workload = estimate_workload(course_ids)
    total_difficulty = sum(calculate_difficulty_score(cid) for cid in course_ids)
    avg_difficulty = total_difficulty / len(course_ids) if course_ids else 0
    
    # Count lab courses
    lab_courses = []
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if course and float(course.get("lab_hours", 0)) > 0:
            lab_courses.append(course_id)
    
    warnings = []
    
    if workload["total_weekly_hours"] > 50:
        warnings.append("Extremely high weekly workload (>50 hours)")
    elif workload["total_weekly_hours"] > 40:
        warnings.append("Very high weekly workload (>40 hours)")
    
    if len(lab_courses) > 2:
        warnings.append(f"Multiple lab courses ({len(lab_courses)}) may have overlapping deadlines")
    
    if avg_difficulty > 7:
        warnings.append("High average course difficulty")
    
    return {
        "is_heavy": len(warnings) > 0,
        "total_weekly_hours": workload["total_weekly_hours"],
        "assessment": workload["assessment"],
        "lab_course_count": len(lab_courses),
        "lab_courses": lab_courses,
        "average_difficulty": round(avg_difficulty, 1),
        "warnings": warnings
    }


def detect_deadline_clusters(course_ids: List[str]) -> Dict[str, Any]:
    """
    Predict weeks with heavy workload overlap.
    
    Args:
        course_ids: List of course IDs
    
    Returns:
        Predicted high-workload weeks
    """
    # Standard academic calendar patterns
    high_workload_weeks = []
    
    # Midterm weeks (weeks 7-9)
    high_workload_weeks.append({
        "week_range": "7-9",
        "period": "Midterm Exams",
        "intensity": "high",
        "description": "Midterm exams and projects typically due"
    })
    
    # Finals week (week 16)
    high_workload_weeks.append({
        "week_range": "16",
        "period": "Finals Week",
        "intensity": "very high",
        "description": "Final exams and end-of-semester projects"
    })
    
    # Check for lab courses
    lab_courses = []
    for course_id in course_ids:
        course = database.get_course_by_id(course_id)
        if course and float(course.get("lab_hours", 0)) > 0:
            lab_courses.append(course_id)
    
    if len(lab_courses) > 1:
        high_workload_weeks.append({
            "week_range": "4-5, 10-11, 14-15",
            "period": "Lab Report Deadlines",
            "intensity": "moderate",
            "description": f"Multiple lab courses ({len(lab_courses)}) may have overlapping lab reports"
        })
    
    # Weekly distribution estimate
    workload = estimate_workload(course_ids)
    base_weekly_hours = workload["total_weekly_hours"]
    
    weekly_distribution = []
    for week in range(1, 17):
        multiplier = 1.0
        
        # Increase workload during midterms and finals
        if 7 <= week <= 9:
            multiplier = 1.5
        elif week == 16:
            multiplier = 2.0
        elif week in [4, 5, 10, 11, 14, 15] and len(lab_courses) > 1:
            multiplier = 1.3
        
        weekly_distribution.append({
            "week": week,
            "estimated_hours": round(base_weekly_hours * multiplier, 1)
        })
    
    return {
        "high_workload_periods": high_workload_weeks,
        "weekly_distribution": weekly_distribution,
        "lab_course_count": len(lab_courses),
        "base_weekly_hours": round(base_weekly_hours, 1)
    }
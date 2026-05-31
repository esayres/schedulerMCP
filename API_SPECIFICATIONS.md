# Appendix A: API Specifications

## Complete MCP Tool Specifications

This appendix provides detailed specifications for all 12 MCP tools implemented in the system.

---

## A.1 Course Discovery Tools

### A.1.1 search_courses

**Signature:**
```python
@mcp.tool()
def search_courses(query: str, semester: str = None) -> Dict[str, Any]
```

**Description:** Search for courses by keyword, department, or course ID.

**Parameters:**
- `query` (str, required): Search term
- `semester` (str, optional): Semester ID (e.g., "spring_2026")

**Returns:** Dictionary containing:
- `semester`: Human-readable semester
- `semester_id`: Machine-readable semester ID
- `query`: Original search query
- `count`: Number of results
- `courses`: Array of course objects

**Example Response:**
```json
{
  "semester": "Spring 2026",
  "semester_id": "spring_2026",
  "query": "computer science",
  "count": 8,
  "courses": [...]
}
```

---

### A.1.2 get_course_info

**Signature:**
```python
@mcp.tool()
def get_course_info(course_id: str, semester: str = None) -> Dict[str, Any]
```

**Description:** Get detailed information about a specific course.

**Parameters:**
- `course_id` (str, required): Course identifier (e.g., "cs120")
- `semester` (str, optional): Semester ID

**Returns:** Dictionary containing complete course details including prerequisites, sections, and metadata.

---

### A.1.3 get_course_sections

**Signature:**
```python
@mcp.tool()
def get_course_sections(course_id: str, semester: str = None) -> Dict[str, Any]
```

**Description:** Get all sections for a specific course.

**Parameters:**
- `course_id` (str, required): Course identifier
- `semester` (str, optional): Semester ID

**Returns:** Dictionary containing section count and array of section objects with meeting times, instructors, and locations.

---

## A.2 Schedule Analysis Tools

### A.2.1 detect_schedule_conflicts

**Signature:**
```python
@mcp.tool()
def detect_schedule_conflicts(
    course_ids: List[str],
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Detect time conflicts between courses.

**Algorithm:**
1. Load course data for specified semester
2. For each pair of courses:
   - Check day overlaps
   - Parse meeting times
   - Detect time overlaps
   - Check additional times (labs)
3. Return all conflicts found

**Complexity:** O(n² × s²) where n = courses, s = sections per course

---

### A.2.2 generate_possible_schedules

**Signature:**
```python
@mcp.tool()
def generate_possible_schedules(
    requested_courses: List[str],
    max_units: int = 18,
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Generate all valid schedule combinations.

**Algorithm:**
1. Validate prerequisites
2. Generate candidate schedule combinations from the requested courses. Each candidate schedule is evaluated against prerequisite, unit, and scheduling constraints. Valid schedules are returned to the user.
3. Return all valid schedules

**Complexity:** O(2ⁿ × n²) with early pruning

---

### A.2.3 suggest_best_schedule

**Signature:**
```python
@mcp.tool()
def suggest_best_schedule(
    requested_courses: List[str],
    preference: str = "balanced",
    max_units: int = 18,
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Suggest the best schedule based on preferences.

**Preference Modes:**
- `balanced`: Distribute classes evenly across week
- `compact`: Minimize number of days on campus
- `no_mornings`: Avoid classes before 10 AM

**Scoring Algorithm:**
```
For each valid schedule:
    score = 0
    
    If preference == "balanced":
        score += balance_score(schedule)
    Elif preference == "compact":
        score += compactness_score(schedule)
    # ... other preferences
    
    Return schedule with highest score
```

---

## A.3 Prerequisite Validation Tools

### A.3.1 validate_prerequisites

**Signature:**
```python
@mcp.tool()
def validate_prerequisites(
    completed_courses: List[str],
    requested_courses: List[str],
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Validate if prerequisites are satisfied.

**Prerequisite Logic:**
- Flat items in array: ALL required (AND logic)
- Nested arrays: ONE required (OR logic)
- Example: `["math150", ["cs130", "cs131"]]` means MATH150 AND (CS130 OR CS131)

**Validation Algorithm:**
```
For each requested course:
    prereqs = course.prerequisites
    
    For each prereq in prereqs:
        If prereq is array:
            satisfied = any(p in completed for p in prereq)
        Else:
            satisfied = prereq in completed
        
        If not satisfied:
            Add to issues
    
    Return overall_valid = (no issues)
```

---

### A.3.2 validate_course_plan

**Signature:**
```python
@mcp.tool()
def validate_course_plan(
    semester_plan: List[List[str]],
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Validate a multi-semester course plan.

**Algorithm:**
```
completed = []

For each semester in plan:
    For each course in semester:
        If not validate_prerequisites(completed, [course]):
            Add error for this semester
        
        completed.append(course)

Return validation results
```

---

## A.4 Workload Estimation Tools

### A.4.1 estimate_semester_workload

**Signature:**
```python
@mcp.tool()
def estimate_semester_workload(
    course_ids: List[str],
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Estimate total weekly workload for a semester.

**Calculation Model:**
```
For each course:
    contact_hours = lecture_hours + lab_hours (per week)
    out_of_class_hours = contact_hours × 2
    total_hours = contact_hours + out_of_class_hours

semester_total = sum(total_hours for all courses)

Assessment:
    < 30 hours: "light"
    30-40 hours: "moderate"
    40-50 hours: "heavy"
    ≥ 50 hours: "very heavy"
```

---

### A.4.2 detect_deadline_clusters

**Signature:**
```python
@mcp.tool()
def detect_deadline_clusters(
    course_ids: List[str],
    semester: str = None
) -> Dict[str, Any]
```

**Description:** Predict busy periods and deadline clusters.

**Model:**
- Weeks 7-9: Midterm exams (+50% workload)
- Week 16: Finals week (+100% workload)
- Lab courses: +20% during project weeks

---

## A.5 Semester Management Tools

### A.5.1 set_semester

**Signature:**
```python
@mcp.tool()
def set_semester(semester: str) -> Dict[str, Any]
```

**Description:** Set the active semester for all subsequent queries.

**Side Effects:** Updates global `SELECTED_SEMESTER` variable.

---

### A.5.2 get_current_semester

**Signature:**
```python
@mcp.tool()
def get_current_semester() -> Dict[str, Any]
```

**Description:** Get information about the currently active semester.

**Returns:** Current semester, course count, and last updated timestamp.

---

## A.6 Data Schemas

### Course Object Schema

```json
{
  "course_id": "string",
  "title": "string",
  "course_title": "string",
  "honors": "boolean",
  "units": "string",
  "description": "string",
  "prereqs": "array",
  "coreqs": "array",
  "advisory": "array",
  "limitation": "array",
  "min_units": "string",
  "max_units": "string",
  "contact_hours": "string",
  "out_of_class_hours": "string",
  "lecture_hours": "string",
  "lab_hours": "string",
  "department": "string",
  "label": "string",
  "sections": "array"
}
```

### Section Object Schema

```json
{
  "crn": "string",
  "section": "string",
  "credits": "string",
  "days": ["array", "of", "strings"],
  "time": "string",
  "location": "string",
  "instructor": "string",
  "status": "string",
  "additional_times": [
    {
      "type": "lab",
      "days": ["array"],
      "time": "string",
      "location": "string"
    }
  ]
}
```

---

## A.7 Error Handling

All tools follow consistent error handling:

**Error Response Format:**
```json
{
  "success":   False,
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

---

## A.8 Performance Characteristics

|       Tool                    | Complexity| Caching       |
|-------------------------------|-----------|---------------|
| search_courses                | O(n)      | In-memory     |
| get_course_info               | O(1)      | Hash index    |
| get_course_sections           | O(1)      | Hash index    |
| detect_schedule_conflicts     | O(n²)     | None          |
| generate_possible_schedules   | O(2ⁿ)     | None          |
| suggest_best_schedule         | O(2ⁿ)     | None          |
| validate_prerequisites        | O(n×m)    | None          |
| validate_course_plan          | O(s×n×m)  | None          |
| estimate_semester_workload    | O(n)      | None          |
| detect_deadline_clusters      | O(n)      | None          |
| set_semester                  | O(1)      | *Auto-scrape  |
| get_current_semester          | O(1)      | Global var    |

*Note: set_semester may trigger auto-scraping if data missing, adding 2-5 minutes one-time cost.

---

*End of API Specifications*

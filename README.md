# MCP Scheduling Tool

A comprehensive course planning and schedule generation system built as an MCP (Model Context Protocol) server. This tool helps students search courses, validate prerequisites, detect schedule conflicts, generate optimal schedules, and estimate workload.

## Features

### Course Discovery
- **Search Courses**: Find courses by keyword, department, or course ID
- **Course Information**: Get detailed course info including prerequisites, units, and workload
- **Section Listing**: View available sections with meeting times (when data available)

### Schedule Planning
- **Conflict Detection**: Identify time overlaps between selected courses
- **Schedule Generation**: Generate all valid schedule combinations
- **Smart Recommendations**: Get the best schedule based on your preferences (balanced, compact, no mornings)

### Academic Planning
- **Prerequisite Validation**: Verify you meet requirements for requested courses
- **Corequisite Checking**: Ensure corequisites are included in your schedule
- **Multi-Semester Planning**: Validate long-term course plans across multiple semesters

### Workload Management
- **Workload Estimation**: Calculate weekly hours including lecture, lab, and study time
- **Deadline Clusters**: Predict busy weeks with overlapping deadlines
- **Heavy Semester Detection**: Get warnings about overloaded schedules

## Installation

### Using UV (Recommended)

```bash
# Install from PyPI (when published)
uv pip install scheduler-mcp

# Or install from source
git clone <repository-url>
cd canvasMCP
uv pip install -e .
```

### Using pip

```bash
pip install scheduler-mcp
```

## Usage

### As an MCP Server

The tool runs as an MCP server using stdio transport, making it compatible with AI assistants and MCP clients.

```bash
# Run the server
scheduler-mcp

# Or use with uvx
uvx scheduler-mcp
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run scheduler-mcp
```

### Available Tools

#### Course Discovery

**search_courses(query, semester="fall_2026")**
```python
# Search for courses
search_courses("computer science")
search_courses("MATH")
```

**get_course_info(course_id, semester="fall_2026")**
```python
# Get detailed course information
get_course_info("acct111")
```

#### Schedule Planning

**detect_schedule_conflicts(course_ids)**
```python
# Check for time conflicts
detect_schedule_conflicts(["cs120", "math150", "acct111"])
```

**generate_possible_schedules(requested_courses, max_units=18)**
```python
# Generate all valid schedules
generate_possible_schedules(["cs120", "math150", "engl101"], max_units=15)
```

**suggest_best_schedule(requested_courses, preference="balanced", max_units=18)**
```python
# Get the best schedule recommendation
suggest_best_schedule(
    ["cs120", "math150", "acct111"],
    preference="no_mornings",
    max_units=18
)
```

Preferences:
- `balanced`: Evenly distributed workload
- `compact`: Dense schedule with minimal gaps
- `no_mornings`: Avoid early morning classes

#### Academic Validation

**validate_prerequisites(completed_courses, requested_courses)**
```python
# Check if prerequisites are satisfied
validate_prerequisites(
    completed_courses=["acct111"],
    requested_courses=["acct113"]
)
```

**validate_course_plan(course_plan)**
```python
# Validate multi-semester plan
validate_course_plan([
    ["cs101", "math140"],  # Semester 1
    ["cs120", "math150"],  # Semester 2
    ["cs220", "cs240"]     # Semester 3
])
```

#### Workload Analysis

**estimate_semester_workload(course_ids)**
```python
# Estimate weekly workload
estimate_semester_workload(["cs120", "math150", "phys201"])
```

**detect_deadline_clusters(course_ids)**
```python
# Predict busy weeks
detect_deadline_clusters(["cs120", "math150", "chem101"])
```

## Example Workflow

```python
# 1. Search for courses
courses = search_courses("accounting")

# 2. Get detailed info
course_info = get_course_info("acct111")

# 3. Validate prerequisites
validation = validate_prerequisites(
    completed_courses=["math101"],
    requested_courses=["acct111", "acct113"]
)

# 4. Generate schedules
schedules = generate_possible_schedules(
    ["acct111", "math150", "engl101"],
    max_units=15
)

# 5. Get best schedule
best = suggest_best_schedule(
    ["acct111", "math150", "engl101"],
    preference="balanced"
)

# 6. Estimate workload
workload = estimate_semester_workload(["acct111", "math150", "engl101"])

# 7. Check for deadline clusters
clusters = detect_deadline_clusters(["acct111", "math150", "engl101"])
```

## Data Format

The tool expects course data in JSON format with the following structure:

```json
{
  "course_id": "acct111",
  "title": "Bookkeeping",
  "course_title": "ACCT 111",
  "units": "3.0 Units",
  "description": "Course description...",
  "prereqs": ["ACCT 101"],
  "coreqs": [],
  "advisory": [],
  "min_units": "3.0",
  "max_units": "3.0",
  "contact_hours": "54.0",
  "out_of_class_hours": "108.0",
  "lecture_hours": "54.0",
  "lab_hours": "0.0",
  "department": "accounting"
}
```

Place course data in `courses.json` or `courses_<semester>.json` in the project root.

## Development

### Project Structure

```
canvasMCP/
├── src/
│   └── canvas_mcp/
│       ├── run.py              # Main entry point with MCP tools
│       ├── database.py         # Course data loading and queries
│       ├── schueduling.py      # Scheduling algorithms
│       ├── workload.py         # Workload estimation
│       ├── tools/
│       │   └── courses.py      # Tool implementations
│       └── tests/
│           ├── testConflicts.py
│           ├── testPrereqs.py
│           └── testSchueduler.py
├── courses.json                # Course data
├── pyproject.toml             # Package configuration
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
uv pip install pytest

# Run tests
pytest src/canvas_mcp/tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Architecture

The MCP Scheduling Tool follows a layered architecture:

1. **MCP Layer** (`run.py`): Exposes tools via FastMCP decorators
2. **Tool Layer** (`tools/courses.py`): Thin wrappers that delegate to core logic
3. **Logic Layer** (`schueduling.py`, `workload.py`): Core algorithms and business logic
4. **Data Layer** (`database.py`): Course data loading and queries

This separation ensures:
- Clean, testable code
- Easy maintenance
- Clear responsibilities
- Reusable components

## Limitations

- Section/meeting time data not yet available in current dataset
- Conflict detection requires section data to be fully functional
- Schedule generation currently simplified without section combinations

## Future Enhancements

- [ ] Add section/meeting time data support
- [ ] Implement full conflict detection with time overlaps
- [ ] Add Canvas API integration for real-time data
- [ ] Support for multiple institutions
- [ ] Web scraping for automatic data updates
- [ ] Visual schedule generation
- [ ] Export to calendar formats (iCal, Google Calendar)

## License

[Your License Here]

## Contact

[Your Contact Information]

## Acknowledgments

Built with [FastMCP](https://github.com/jlowin/fastmcp) - A fast, simple framework for building MCP servers.

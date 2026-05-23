# Quick Start Guide

Get up and running with the MCP Scheduling Tool in 5 minutes.

## Installation

### Option 1: Using UV (Recommended)

```bash
# Install from source
git clone <repository-url>
cd canvasMCP
uv pip install -e .
```

### Option 2: Using pip

```bash
pip install -e .
```

## Verify Installation

```bash
# Check that the command is available
scheduler-mcp --help

# Or run directly
python -m canvas_mcp.run
```

## Test with MCP Inspector

The easiest way to test your MCP server is with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run scheduler-mcp
```

This will open a web interface where you can:
1. See all available tools
2. Test tool invocations
3. View responses

## Basic Usage Examples

### Example 1: Search for Courses

```python
# In MCP Inspector or via AI assistant
search_courses("accounting")
```

**Response:**
```json
[
  {
    "course_id": "acct111",
    "title": "Bookkeeping",
    "units": "3.0",
    "department": "accounting",
    "description": "Students will learn introductory theory..."
  },
  ...
]
```

### Example 2: Get Course Details

```python
get_course_info("acct111")
```

**Response:**
```json
{
  "course_id": "acct111",
  "title": "Bookkeeping",
  "description": "Full description...",
  "units": "3.0",
  "prerequisites": [],
  "corequisites": [],
  "lecture_hours": "54.0",
  "lab_hours": "0.0",
  ...
}
```

### Example 3: Validate Prerequisites

```python
validate_prerequisites(
    completed_courses=["acct111"],
    requested_courses=["acct113"]
)
```

**Response:**
```json
{
  "prerequisites_valid": true,
  "corequisites_valid": true,
  "overall_valid": true,
  "prerequisite_issues": [],
  "corequisite_issues": [],
  "message": "All requirements satisfied"
}
```

### Example 4: Generate Schedules

```python
generate_possible_schedules(
    requested_courses=["acct111", "acct115", "acct121"],
    max_units=18
)
```

**Response:**
```json
[
  {
    "courses": ["acct111", "acct115", "acct121"],
    "total_units": 8.0,
    "conflicts": [],
    "valid": true
  }
]
```

### Example 5: Get Best Schedule

```python
suggest_best_schedule(
    requested_courses=["acct111", "acct115", "acct121"],
    preference="balanced",
    max_units=18
)
```

**Response:**
```json
{
  "schedule": {
    "courses": ["acct111", "acct115", "acct121"],
    "total_units": 8.0,
    "score": 135.0,
    "valid": true
  },
  "preference": "balanced",
  "message": "Best schedule found with score 135.0"
}
```

### Example 6: Estimate Workload

```python
estimate_semester_workload(["acct111", "acct115", "acct121"])
```

**Response:**
```json
{
  "total_contact_hours": 9.0,
  "total_out_of_class_hours": 18.0,
  "total_weekly_hours": 27.0,
  "assessment": "moderate",
  "course_breakdown": [
    {
      "course_id": "acct111",
      "title": "Bookkeeping",
      "weekly_contact_hours": 3.0,
      "weekly_out_of_class_hours": 6.0,
      "weekly_total_hours": 9.0
    },
    ...
  ],
  "is_heavy_semester": false,
  "warnings": []
}
```

### Example 7: Detect Deadline Clusters

```python
detect_deadline_clusters(["acct111", "acct121"])
```

**Response:**
```json
{
  "high_workload_periods": [
    {
      "week_range": "7-9",
      "period": "Midterm Exams",
      "intensity": "high",
      "description": "Midterm exams and projects typically due"
    },
    {
      "week_range": "16",
      "period": "Finals Week",
      "intensity": "very high",
      "description": "Final exams and end-of-semester projects"
    }
  ],
  "weekly_distribution": [
    {"week": 1, "estimated_hours": 18.0},
    {"week": 2, "estimated_hours": 18.0},
    ...
  ],
  "lab_course_count": 1,
  "base_weekly_hours": 18.0
}
```

## Using with AI Assistants

### Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "scheduler": {
      "command": "scheduler-mcp"
    }
  }
}
```

Then ask Claude:
- "Search for computer science courses"
- "What are the prerequisites for ACCT 113?"
- "Generate a schedule with CS120, MATH150, and ENGL101"
- "Estimate the workload for my schedule"

### Other MCP Clients

Any MCP-compatible client can use the scheduler-mcp server via stdio transport.

## Common Workflows

### Workflow 1: Planning a Semester

```python
# 1. Search for courses
courses = search_courses("computer science")

# 2. Get details for interesting courses
cs120 = get_course_info("cs120")
cs220 = get_course_info("cs220")

# 3. Validate prerequisites
validation = validate_prerequisites(
    completed_courses=["cs101"],
    requested_courses=["cs120", "cs220"]
)

# 4. Generate schedules
schedules = generate_possible_schedules(
    ["cs120", "math150", "engl101"],
    max_units=15
)

# 5. Get best schedule
best = suggest_best_schedule(
    ["cs120", "math150", "engl101"],
    preference="balanced"
)

# 6. Check workload
workload = estimate_semester_workload(["cs120", "math150", "engl101"])
```

### Workflow 2: Multi-Semester Planning

```python
# Validate a 3-semester plan
plan = validate_course_plan([
    ["cs101", "math140"],      # Semester 1
    ["cs120", "math150"],      # Semester 2
    ["cs220", "cs240"]         # Semester 3
])

if plan["valid"]:
    print("Your plan is valid!")
else:
    print("Issues found:")
    for error in plan["errors"]:
        print(f"  Semester {error['semester']}: {error['issue']}")
```

## Running Tests

```bash
# Run all tests
pytest src/canvas_mcp/tests/

# Run specific test file
pytest src/canvas_mcp/tests/testPrereqs.py -v

# Run with coverage
pytest src/canvas_mcp/tests/ --cov=canvas_mcp
```

## Troubleshooting

### Issue: "Course data not found"

**Solution**: Make sure `courses.json` exists in the project root directory.

### Issue: "Module not found"

**Solution**: Install the package in development mode:
```bash
uv pip install -e .
```

### Issue: "MCP Inspector won't connect"

**Solution**: Make sure the server starts correctly:
```bash
scheduler-mcp
# Should start without errors
```

### Issue: "No courses returned"

**Solution**: Check that course data is loaded:
```python
from canvas_mcp import database
database.load_courses()
print(f"Loaded {len(database.COURSES)} courses")
```

## Next Steps

1. Read the [API Specifications](src/canvas_mcp/docs/apiSpecs.md) for detailed tool documentation
2. Review the [Architecture Documentation](src/canvas_mcp/docs/architecture.md) to understand the system design
3. Check the [Research Notes](src/canvas_mcp/docs/researchNotes.md) for design decisions and trade-offs
4. Explore the test files for more usage examples

## Getting Help

- Check the [README](README.md) for comprehensive documentation
- Review the [API Specifications](src/canvas_mcp/docs/apiSpecs.md) for tool details
- Look at test files for code examples
- Open an issue on GitHub for bugs or questions

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

Happy scheduling! 🎓

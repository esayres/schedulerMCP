# Scheduler MCP - AI-Powered Course Planning

[![PyPI version](https://badge.fury.io/py/scheduler-mcp.svg)](https://pypi.org/project/scheduler-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive course planning and schedule generation system built as an MCP (Model Context Protocol) server for Antelope Valley College. This tool helps students search courses, validate prerequisites, detect schedule conflicts, generate optimal schedules, and estimate workload.

**Now available on PyPI and hosted on Railway for instant access!**

## Quick Start

### Option 1: Use Hosted Server (Recommended)

Connect to our hosted Railway server - **no installation needed**!

#### For Claude Desktop

Add to your MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "scheduler-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://schedulermcp-production.up.railway.app/mcp",
        "--allow-http"
      ]
    }
  }
}
```

#### For Other MCP Clients

Use the endpoint:
```
https://schedulermcp-production.up.railway.app/mcp
```

### Option 2: Install from PyPI

```bash
# Using pip
pip install scheduler-mcp

# Using uv (recommended)
uv pip install scheduler-mcp

# Using uvx (no installation, run directly)
uvx scheduler-mcp
```

### Option 3: Install from Source

```bash
git clone https://github.com/yourusername/schedulerMCP.git
cd schedulerMCP
pip install -e .
```

## Features

### 🔍 Course Discovery
- **Search Courses**: Find courses by keyword, department, or course ID
- **Course Information**: Get detailed course info including prerequisites, units, and workload
- **Section Listing**: View available sections with meeting times and instructors
- **Lab Times**: See laboratory session times separately from lectures

### 📅 Schedule Planning
- **Conflict Detection**: Identify time overlaps between selected courses (including labs!)
- **Schedule Generation**: Generate all valid schedule combinations
- **Smart Recommendations**: Get the best schedule based on your preferences (balanced, compact, no mornings)
- **Semester Context**: All responses include which semester you're viewing

### 🎓 Academic Planning
- **Prerequisite Validation**: Verify you meet requirements for requested courses
  - Handles complex AND/OR logic (e.g., "MATH150 AND (CS130 OR CS131)")
- **Corequisite Checking**: Ensure corequisites are included in your schedule
- **Multi-Semester Planning**: Validate long-term course plans across multiple semesters

### 📊 Workload Management
- **Workload Estimation**: Calculate weekly hours including lecture, lab, and study time
- **Deadline Clusters**: Predict busy weeks with overlapping deadlines
- **Heavy Semester Detection**: Get warnings about overloaded schedules

### 🌐 Web Scraping
- **Automatic Data Collection**: Scrapes AVC course catalog and schedule
- **Parallel Processing**: 5x faster scraping with concurrent requests
- **Semester Management**: Auto-detects current semester and manages data files

## Usage Examples

### With Claude Desktop

Once configured, just ask Claude natural language questions:

```
"What computer science courses are available for Spring 2026 semester?"

"Can I take CS150 if I've completed MATH150 and CS130?"

"Generate a schedule with CS120, MATH150, and ENGL101 that avoids morning classes"

"How many hours per week is this schedule?"
```

### With MCP Inspector

Test the server locally:

```bash
npx @modelcontextprotocol/inspector uvx scheduler-mcp
```

### Programmatic Usage

```python
from scheduler_mcp import database, schueduling

# Load course data
database.load_courses()

# Search for courses
results = database.search_courses("computer science")

# Validate prerequisites
validation = schueduling.validate_prerequisites(
    completed_courses=["math150", "cs130"],
    requested_courses=["cs150"]
)

# Detect conflicts
conflicts = schueduling.detect_conflicts(["cs120", "math150"])

# Generate schedules
schedules = schueduling.generate_schedules(
    ["cs120", "math150", "engl101"],
    max_units=18
)
```

## Available MCP Tools

The server exposes 12 MCP tools:

**(check API_SPECIFICATIONS.md for more help!)**

### Course Discovery
1. **search_courses**(query, semester) - Search for courses
2. **get_course_info**(course_id, semester) - Get detailed course information
3. **get_course_sections**(course_id, semester) - Get course sections with times

### Schedule Analysis
4. **detect_schedule_conflicts**(course_ids, semester) - Find time conflicts
5. **generate_possible_schedules**(courses, max_units, semester) - Generate valid schedules
6. **suggest_best_schedule**(courses, preference, max_units, semester) - Get best schedule

### Prerequisite Validation
7. **validate_prerequisites**(completed, requested, semester) - Check prerequisites
8. **validate_course_plan**(semester_plan, semester) - Validate multi-semester plan

### Workload Estimation
9. **estimate_semester_workload**(course_ids, semester) - Calculate weekly hours
10. **detect_deadline_clusters**(course_ids, semester) - Predict busy periods

### Semester Management
11. **set_semester**(semester) - Change active semester
12. **get_current_semester**() - Get current semester info

## Data Collection

The system automatically scrapes course data from AVC's website:

```bash
# Manual scraping (optional - happens automatically when needed)
python src/scheduler_mcp/webscrapper/unified_scraper.py

# Scrapes:
# - Course catalog (titles, descriptions, prerequisites)
# - Schedule (sections, meeting times, instructors, labs)
# - Merges data into courses_<semester>.json
```

**Performance:**
- Parallel scraping: 2-5 minutes (5x faster than sequential)
- Data cached per semester
- Auto-scrapes when semester data missing

## Project Structure

```
schedulerMCP/
├── src/
│   └── scheduler_mcp/
│       ├── run.py                    # MCP server with HTTPS support
│       ├── database.py               # Course data loading and queries
│       ├── schueduling.py            # Scheduling algorithms
│       ├── workload.py               # Workload estimation
│       ├── semesterSync.py           # Semester management
│       ├── data/                     # Course data directory
│       │   ├── courses.json          # Default course database
│       │   └── courses_*.json        # Semester-specific databases
│       ├── tools/
│       │   └── courses.py            # Tool implementations
│       ├── webscrapper/
│       │   ├── unified_scraper.py    # Main scraper
│       │   ├── allCoursesScrapper.py # Catalog scraper
│       │   └── schuedulerScrapper.py # Schedule scraper
│       └── tests/
│           ├── testConflicts.py      # Conflict detection tests
│           ├── testPrereqs.py        # Prerequisite validation tests
│           └── testSchueduler.py     # Schedule generation tests
├── pyproject.toml                    # Package configuration
├── README.md                         # This file
└── LICENSE                           # MIT License
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest src/scheduler_mcp/tests/

# Run specific test file
pytest src/scheduler_mcp/tests/testPrereqs.py -v

# Run with coverage
pytest src/scheduler_mcp/tests/ --cov=scheduler_mcp
```

### Local Development

```bash
# Install in development mode
pip install -e .

# Run MCP server locally
scheduler-mcp

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uvx scheduler-mcp
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Architecture

The system follows a layered architecture:

```
┌─────────────────────────────────────────┐
│    MCP Interface Layer (HTTPS)          │  ← AI Assistant Integration
├─────────────────────────────────────────┤
│    Tool Implementation Layer            │  ← Business Logic
├─────────────────────────────────────────┤
│    Core Logic Layer                     │  ← Algorithms
│  (Scheduling, Validation, Workload)     │
├─────────────────────────────────────────┤
│    Data Collection Layer                │  ← Web Scraping
│  (Catalog, Schedule, Merging)           │
└─────────────────────────────────────────┘
```

**Key Design Principles:**
- **Separation of Concerns**: Clear boundaries between layers
- **Stateful Context**: Persistent semester selection across tool invocations

## Technical Highlights

### Prerequisite Parsing
- Handles AND/OR logic with nested arrays
- Example: `["MATH150", ["CS130", "CS131"]]` means MATH150 AND (CS130 OR CS131)
- Filters metadata (C-ID, Formerly, etc.) before parsing

### Web Scraping
- **Parallel Processing**: ThreadPoolExecutor with 5 workers
- **TBA Course Handling**: Detects `colspan` attributes for proper parsing
- **Lab Time Extraction**: Associates lab sessions with lecture sections
- **Course ID Normalization**: high merge accuracy between catalog and schedule

## Deployment

### Railway (Production)

The server is deployed on Railway at:
```
https://schedulermcp-production.up.railway.app/mcp
```

**Features:**
- HTTPS support
- Automatic updates from main branch
- Environment variable configuration


## Limitations

- **Single Institution**: Currently AVC-specific (scraper tied to AVC's HTML structure)
- **No Real-Time Enrollment**: Cannot track seat availability or waitlists
- **Semester-Based Updates**: Data updated per semester, not continuously
- **Basic Optimization**: Simple preference modes (no multi-objective optimization)

## Future Enhancements

- [ ] Canvas API integration for real-time enrollment data
- [ ] Multi-institution support with configurable scrapers
- [ ] Visual schedule generation (calendar view)
- [ ] Export to Apple Calendar/Google Calendar
- [ ] Machine learning for schedule recommendations

## Research Paper

This project was developed as part of a course assignment on MCP servers. See `RESEARCH_PAPER.md` for the full research paper.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contact

**Author:** Elijah Sayres  
**Email:** elijahsayres@gmail.com  
**Institution:** Antelope Valley College  

## Acknowledgments

- Antelope Valley College for course data
- FastMCP team for the excellent Python MCP SDK
- Model Context Protocol creators for the open standard
- Railway for hosting infrastructure

## Links

- **PyPI**: https://pypi.org/project/scheduler-mcp/
- **Railway**: https://schedulermcp-production.up.railway.app/mcp
- **GitHub**: https://github.com/esayres/schedulerMCP
---

**Made with ❤️ for AVC students**

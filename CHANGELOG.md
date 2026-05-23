# Changelog

All notable changes to the MCP Scheduling Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-XX

### Added
- Initial release of MCP Scheduling Tool
- Course discovery tools:
  - `search_courses`: Search by keyword, department, or course ID
  - `get_course_info`: Get detailed course information
  - `get_course_sections`: Get course sections (placeholder)
- Schedule analysis tools:
  - `detect_schedule_conflicts`: Detect time conflicts
  - `generate_possible_schedules`: Generate valid schedules
  - `suggest_best_schedule`: Get best schedule recommendation
- Prerequisite validation tools:
  - `validate_prerequisites`: Validate prerequisites and corequisites
  - `validate_course_plan`: Validate multi-semester plans
- Workload estimation tools:
  - `estimate_semester_workload`: Calculate weekly workload
  - `detect_deadline_clusters`: Predict busy weeks
- Comprehensive test suite with pytest
- Complete API documentation
- Architecture documentation
- Research notes and design decisions
- README with installation and usage instructions

### Known Limitations
- Section/meeting time data not yet available
- Conflict detection simplified without time data
- Schedule generation without section combinations
- Prerequisite logic uses simple OR (any prerequisite satisfies)

## [Unreleased]

### Planned Features
- Section/meeting time data integration
- Real-time conflict detection with time overlaps
- Advanced schedule optimization algorithms
- Canvas API integration
- Multi-institution support
- Web scraping for automatic data updates
- Visual schedule generation
- Export to calendar formats (iCal, Google Calendar)

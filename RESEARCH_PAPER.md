# Design and Implementation of an MCP-Based Course Planning System

**Elijah Sayres**

Antelope Valley College

Computer Science Department

*CS 230 **-** May 2026*

# Abstract

Academic course planning can be challenging for students because it requires managing prerequisite chains, avoiding schedule conflicts, and balancing workload across a semester. This paper presents an AI-assisted course planning system built using the Model Context Protocol (MCP). An MCP server was developed that combines web scraping, prerequisite validation, schedule conflict detection, and workload estimation to provide course planning tools through a natural language interface.

The system supports complex prerequisite requirements containing nested AND/OR logic, detects scheduling conflicts including laboratory sections, and estimates weekly student workload. Performance improvements using parallel web scraping reduced data collection time from approximately 15–20 minutes to 2–5 minutes. The system achieved a high course data merge rate and successfully validated prerequisite chains using real course catalog data. The project was developed for Antelope Valley College Course CS 230 and distributed through PyPI for future use and expansion.

This project demonstrates how AI assistants can be combined with domain-specific tools to help students make more informed academic planning decisions.

# 1. Introduction

## 1.1 Motivation

Planning a college schedule is often more difficult than simply choosing classes. Students must verify prerequisites, avoid scheduling conflicts, estimate workload, and plan multiple semesters ahead to stay on track for graduation. At many colleges, this information is spread across multiple websites and documents, making the planning process time-consuming and prone to mistakes.

Recent advances in large language models (LLMs) have made it possible to interact with software systems using natural language. However, LLMs do not have direct access to institutional course data or the specialized logic needed to validate schedules and prerequisites. The Model Context Protocol (MCP) provides a way for AI assistants to access external tools and data sources, making it possible to combine natural language interaction with domain-specific functionality.

## 1.2 Problem Statement

Students at Antelope Valley College (AVC) face several challenges when planning their schedules:

- **Prerequisite Complexity:** Many courses contain prerequisite requirements with AND/OR relationships (for example, "MATH 150 AND (CS 130 OR CS 131 OR CS 132)").

- **Schedule Conflicts:** Identifying overlapping lecture and laboratory times can be tedious when done manually.

- **Workload Management:** Students often have limited information about the total time commitment required for a semester.

- **Multi-Semester Planning:** Tracking prerequisite chains across future semesters can be difficult.

- **Data Accessibility:** Course information is distributed across multiple web pages without a centralized public API.

## 1.3 Contributions

The main contributions of this project are:

- System Design: Design and implementation of an MCP-based course planning system.

- Prerequisite Parsing: Development of a parser that extracts and validates prerequisite requirements from course descriptions.

- Performance Optimization: Implementation of parallel web scraping techniques that reduced data collection time by approximately 5×.

- Production Deployment: Creation of a fully functional system for Antelope Valley College that is distributed through PyPI.

- Empirical Evaluation: Analysis of system performance and accuracy using real course catalog and schedule data.

## 1.4 Paper Organization

The remainder of this paper is organized as follows. Section 2 reviews related work in course scheduling and educational technology. Section 3 describes the system architecture and design decisions. Section 4 explains the algorithms used for prerequisite validation, conflict detection, and schedule generation. Section 5 discusses implementation details and performance optimizations. Section 6 presents evaluation results. Section 7 discusses limitations and future work. Section 8 concludes the paper.

# 2. Related Work

## 2.1 Course Scheduling Systems

Academic course scheduling has been widely studied in operations research and computer science. Burke and Petrovic (2002) provide a survey of automated timetabling research and discuss challenges such as constraint satisfaction, optimization objectives, and computational complexity.

Most of the systems discussed by Burke and Petrovic focus on institutional scheduling problems, where universities assign courses, rooms, and times while satisfying various constraints. In contrast, this project focuses on student-centered schedule planning. Instead of generating an institutional timetable, the system helps students select courses, verify prerequisites, and identify scheduling conflicts using an existing timetable.

## 2.2 Prerequisite Dependency Analysis

Slim et al. (2014) modeled university curricula as directed acyclic graphs (DAGs) and showed how prerequisite relationships can affect student progress through degree programs. Their work highlights the importance of understanding prerequisite structures when planning academic pathways.

This project applies those ideas in a practical setting by implementing prerequisite validation for course planning. Unlike graph-based curriculum models, the system extracts prerequisite information directly from course descriptions and supports both simple and nested AND/OR prerequisite relationships.

## 2.3 Educational Recommender Systems

Researchers have also explored course recommendation systems. Elbadrawy et al. (2016) used predictive analytics to estimate student performance and recommend courses, while O'Mahony and Smyth (2007) developed a recommendation system based on previous enrollment patterns.

These systems focus primarily on recommending which courses students should take. In comparison, this project focuses on validating schedules, checking prerequisites, detecting conflicts, and estimating workload after courses have been selected.

## 2.4 AI Assistants and Tool Use

Recent research has explored ways to extend large language models with external tools. Schick et al. (2023) introduced Toolformer, a framework that allows language models to learn when to use APIs. Parisi et al. (2022) surveyed tool-augmented language models and discussed challenges related to tool selection and integration.

The Model Context Protocol (MCP) provides a standardized approach for connecting AI assistants to external tools. This project applies MCP in an educational setting and demonstrates how custom tools can improve the usefulness of AI assistants for academic planning tasks.

## 2.5 Web Scraping for Educational Data

Mitchell (2018) discusses techniques and best practices for collecting data from websites. Since many educational institutions do not provide public APIs for course information, web scraping is often necessary to access catalog and scheduling data.

This project applies web scraping techniques to collect and combine course catalog and schedule information. Special attention was given to handling complex HTML structures, including merged table cells and multi-row course listings for laboratory sections.

# 3. System Architecture

## 3.1 Design Principles

The system was designed around three main principles:

- Separation of Concerns: Data collection, business logic, and interface components are organized into separate layers.

- Stateful Context: Semester selections remain available across multiple tool invocations to support conversational interactions.

- Performance First: The system is optimized to provide fast responses after initial data collection and processing.

## 3.2 Layered Architecture

The system consists of four layers:

```
┌─────────────────────────────────────────┐
│   MCP Interface Layer (FastMCP)         │  ← AI Assistant Integration
├─────────────────────────────────────────┤
│   Tool Implementation Layer             │  ← Business Logic
├─────────────────────────────────────────┤
│   Core Logic Layer                      │  ← Algorithms
│   (Scheduling, Validation, Workload)    │
├─────────────────────────────────────────┤
│   Data Collection Layer                 │  ← Web Scraping
│   (Catalog, Schedule, Merging)          │
└─────────────────────────────────────────┘
```

*Figure 1. System Architecture — Four-Layer Design*

**MCP Interface Layer:** Provides access to 12 tools through a FastMCP server using stdio transport. This layer handles parameter validation, type conversion, and communication between the AI assistant and backend tools.

**Tool Implementation Layer:** Coordinates calls to backend modules, formats responses, and manages semester-specific context.

**Core Logic Layer:** Contains the main algorithms used for prerequisite validation, schedule conflict detection, schedule generation, and workload estimation.

**Data Collection Layer:** Collects course catalog and schedule information through web scraping, parses HTML content, normalizes course identifiers, and merges data from multiple sources.

## 3.3 Data Flow

Course planning queries follow this workflow:

- The user asks an AI assistant a course planning question.

- AI assistant invokes the appropriate MCP tool.

- The tool checks for the required semester dataset.

- If the dataset does not exist, course information is automatically scraped and processed.

- The requested scheduling or validation logic is executed.

- Results are returned along with semester information.

- The AI assistant presents the results in natural language.

This workflow allows users to ask follow-up questions without repeatedly specifying the semester being discussed.

# 4. Algorithms and Methods

## 4.1 Prerequisite Parsing

**Challenge:** Course prerequisites are often written in natural language and may contain complex combinations of AND/OR requirements. For example:

*"**Prerequisite: Completion of MATH 150 or MATH 150H and completion of CS 130 or CS 131 or CS 132.**"*

**Approach:** A two-stage parser was developed to extract and validate prerequisite information from course descriptions.

**Phase 1 — Metadata Removal:**

```
Remove patterns such as: (C-ID: ...) (Formerly ...) (...)

Extract prerequisite statement
```

**Phase 2 — Logical Structure Extraction:**

```
Split prerequisite statement on "and"

For each section:

    Split on "or"

    If multiple options exist:

        Store as nested list

    Else:

        Store as individual requirement
```

Prerequisites are represented using nested data structures where individual items represent AND requirements and nested lists represent OR requirements. Example output:

```
["math150", ["cs130", "cs131", "cs132"]]
```

**Validation Algorithm:**

```
For each prerequisite:

    If prerequisite is a nested list:

        Check whether any option is completed

    Else:

        Check whether the course is completed

    If requirement is not satisfied:

        Add issue to results

Return validation status
```

**Complexity:** O(n × m), where n is the number of requested courses and m is the average number of prerequisite requirements per course.

## 4.2 Schedule Conflict Detection

**Challenge:** Detecting scheduling conflicts requires checking both lecture and laboratory meeting times. Laboratory sessions are often stored separately within the schedule data.

**Time Parsing:**

```
Parse time string "10:00am - 11:50am":

    Extract start_hour, start_minute, start_period

    Extract end_hour, end_minute, end_period

    Convert to 24-hour format

    Return (start_time, end_time)
```

**Conflict Detection Algorithm:**

```
For each course pair:

    Compare meeting days

    If meeting days overlap:

        Compare time ranges

        If overlap exists:

            Record conflict

Repeat process for laboratory sessions
```

**Complexity:** O(n² × s²), where n is the number of courses and s is the average number of available sections. Once a conflict is detected between two course selections, additional comparisons can be skipped for that pair.

## 4.3 Schedule Generation

**Challenge:** Generate valid schedules while respecting prerequisite requirements, scheduling constraints, and unit limits.

**Constraint-Based Search Algorithm:**

```
Validate prerequisites

Generate course combinations

For each combination:

    Calculate total units

    If unit limit exceeded:

        Skip combination

    Check for scheduling conflicts

    If no conflicts:

        Store schedule
```

**Complexity:** O(2ⁿ × n² × s²). Although worst-case complexity is exponential, early pruning significantly reduces the search space. For typical scheduling requests involving three to five courses.

## 4.4 Workload Estimation

Workload estimates are based on the Carnegie Unit guideline, which suggests that one credit hour corresponds to approximately three hours of work per week.

**Workload Calculation:**

```
For each course:

    Contact Hours = Lecture Hours + Lab Hours

    Outside Work = Contact Hours × 2

    Total Workload = Contact Hours + Outside Work

Semester Workload = Sum of all course workloads

Assessment thresholds:

    Semester total < 30 hrs/week  → "light"

    30 ≤ semester total < 40       → "moderate"

    40 ≤ semester total < 50       → "heavy"

    Semester total ≥ 50            → "very heavy"
```

Deadline Clustering: The system also identifies high-effort periods, such as midterm weeks (Weeks 7–9), final exams (Week 16), and project-heavy laboratory courses (+20% workload during project weeks).

# 5. Implementation

## 5.1 Web Scraping Optimization

**Challenge:** Initial data collection required sequential scraping of more than 30 academic departments, resulting in execution times between 15 and 20 minutes.

**Solution:** Parallel scraping using Python's ThreadPoolExecutor.

```python
with ThreadPoolExecutor(max_workers=5) as executor:

    futures = {

        executor.submit(scrape_department, dept): dept

        for dept in departments

    }

    for future in as_completed(futures):

        courses = future.result()

        all_courses.extend(courses)
```

Performance results:

- Sequential scraping: 15–20 minutes

- Parallel scraping (5 workers): 2–5 minutes

- Speedup: approximately 5×

Trade-offs include increased memory usage, higher CPU utilization, and improved overall network throughput.

## 5.2 Course ID Normalization

**Challenge:** Inconsistencies between course identifiers collected from schedule and catalog data sources prevented correct record merging. The schedule scraper generated identifiers such as phys211-generalphysics, while the catalog used simpler identifiers like phys211.

**Solution:**

```
Extract course code BEFORE title separator:

    If " - " in course_name:

        course_code ← course_name.split(" - ")[0]

    course_id ← course_code.replace(" ", "").lower()
```

After implementing this fix, most course records were merged successfully, producing a much more complete dataset for schedule generation and prerequisite validation.

## 5.3 HTML Structure Handling

Several challenges were encountered while scraping course data from the AVC website.

**Challenge 1 — TBA Courses:** Courses with "To Be Assigned" times use colspan="8", shifting cell indices by 7 positions. The scraper was modified to dynamically check for colspan attributes and adjust field locations accordingly.

**Challenge 2 — Lab Times:** Laboratory sections were stored in separate rows without a course identifier. The scraper was modified to examine neighboring rows and associate laboratory meeting times with the correct lecture section, enabling accurate schedule conflict detection.

## 5.4 Semester Context Management

**Challenge:** Users should not need to repeatedly specify the semester during every interaction. The system maintains a selected semester that is automatically applied when tools are called.

```python
# Global state

SELECTED_SEMESTER = "spring_2026"

# All responses include context

def tool_function(params, semester=None):

    if semester is None:

        semester = SELECTED_SEMESTER

    result = execute_logic(params, semester)

    return {

        "semester": format_semester(semester),

        "semester_id": semester,

        "data": result

    }
```

Benefits of this approach include reduced repetitive user input, more natural planning conversations, and simplified semester switching when needed.

# 6. Evaluation

## 6.1 System Performance

After course data is collected and stored locally, most operations execute quickly since the information is loaded from memory rather than being recomputed or re-fetched.

During testing, course searches, prerequisite validation, conflict detection, and workload calculations typically completed in under a second for small to moderate inputs. Schedule generation required additional processing time due to evaluating multiple course combinations, though performance remained acceptable for typical student planning use cases.

The most noticeable improvement came from parallelizing web scraping. Initial data collection required approximately 15–20 minutes when departments were scraped sequentially. Concurrent requests reduced this to roughly 2–5 minutes, significantly improving system usability.

## 6.2 Functional Testing

Testing focused on verifying the core features of the system.

**Prerequisite Validation:** Multiple courses with both simple and complex prerequisite structures were used to test the parser's handling of AND/OR relationships. In most test cases, the system correctly identified missing prerequisites and produced explanations when requirements were not satisfied. Edge cases involving unconventional prerequisite formatting occasionally required manual interpretation.

**Schedule Conflict Detection:** Several course combinations with overlapping lecture and laboratory times were evaluated. The system successfully identified time conflicts in the tested scenarios, including cases where lab sections were stored separately from lecture sections.

**Course Data Integration:** Catalog and schedule datasets were compared after the merging process. Most course records were successfully matched following identifier normalization, though some inconsistencies remained in a small number of edge cases depending on source formatting.

## 6.3 Observations

Testing demonstrated that integrating MCP tools with academic scheduling data can provide a practical natural-language interface for course planning. The system was able to:

- Search and retrieve course information

- Validate prerequisite requirements

- Detect schedule conflicts

- Estimate semester workload

- Maintain semester context across conversations

These results suggest that AI-assisted planning tools can reduce the manual effort required to navigate distributed course information, although effectiveness depends on data consistency and scraping reliability.

# 7. Limitations and Future Work

## 7.1 Current Limitations

**Data Freshness:** The system relies on web-scraped data rather than a real-time institutional API. Schedule changes that occur after data collection may not be reflected immediately.

**Scraper Fragility:** If the structure of AVC's HTML pages changes, the scraper may break or produce incomplete data.

**Enrollment Data:** Current functionality does not include seat availability, waitlist information, or enrollment forecasting. Students must still verify enrollment status through official college systems.

**Prerequisite Complexity:** While the parser handles many common prerequisite structures, some requirements, such as minimum grade thresholds, instructor approval conditions, and concurrent enrollment,  remain difficult to interpret automatically.

**Single Institution:** The current implementation was developed specifically for Antelope Valley College. Adapting the system to another institution would require modifications to data collection and parsing logic.

**Schedule Optimization:** Schedule generation currently focuses on prerequisite validation and conflict avoidance. Additional factors such as instructor preferences, commute time, and personal scheduling preferences are not yet considered.

## 7.2 Future Work

Short-term enhancements:

- Canvas API Integration: Integrate with the Canvas LMS API to access real-time enrollment information, seat availability, and course-related student data.

- Degree Audit Integration: Add support for degree audits to help students verify that planned courses satisfy graduation and transfer requirements.

- Visual Schedule Generation: Allow schedules to be exported to Google Calendar, Apple Calendar, and PDF formats for easier organization.

Long-term research directions:

- Course Recommendation System: Use machine learning to recommend courses based on enrollment patterns, completed coursework, and student goals.

- Advanced Schedule Optimization: Consider workload balance, preferred class times, instructor preferences, and commute time in schedule generation.

- Multi-Institution Support: Expand the system architecture through configurable data collection modules.

- Collaborative Planning Features: Help students coordinate schedules, find study partners, and share academic plans.

- Predictive Analytics: Explore methods for predicting course demand, enrollment trends, and graduation timelines.

## 7.3 Potential Benefits and Considerations

The system has the potential to make course planning more efficient and accessible for students by reducing research time, identifying missing prerequisites, detecting conflicts automatically, and providing workload estimates through natural language interactions.

Students should continue to verify important academic decisions with counselors and advisors. If future versions include personalized data, student information should be handled securely, and access should remain available to all students to avoid creating barriers to academic planning.

# 8. Conclusion

This project presented an AI-assisted course planning system built using the Model Context Protocol (MCP). The system combines web scraping, prerequisite validation, schedule conflict detection, and workload estimation to help students plan courses through natural language interactions.

Several technical challenges were addressed during development, including parsing prerequisite requirements, merging course data from multiple sources, handling complex schedule formats, and improving scraping performance through parallel processing. Testing showed that the system was able to successfully retrieve course information, validate prerequisites, detect schedule conflicts, and maintain semester context across conversations.

The project demonstrates how MCP can be used to connect AI assistants with specialized academic planning tools. By combining AI with institution-specific scheduling data, students can access information more efficiently and receive assistance with tasks that would otherwise require significant manual effort.

Future development will focus on Canvas integration, degree requirement tracking, improved schedule optimization, and support for additional institutions. These improvements could make the system a more comprehensive academic planning tool while continuing to simplify the course scheduling process for students.

# Acknowledgments

This project was completed as part of coursework for CS 230 at Antelope Valley College.

I would like to thank Dr. Kyu Lee for his guidance, feedback, and support throughout the development of this project & course. I would also like to thank the FastMCP development team for providing the Python MCP SDK and the creators of the Model Context Protocol for making the framework publicly available to developers.

# References

Burke, E. K., & Petrovic, S. (2002). Recent research directions in automated timetabling. European Journal of Operational Research, 140(2), 266–280.

Elbadrawy, A., Polyzou, A., Ren, Z., Sweeney, M., Karypis, G., & Rangwala, H. (2016). Predicting student performance using personalized analytics. Computer, 49(4), 61–69.

Mitchell, R. (2018). Web Scraping with Python: Collecting More Data from the Modern Web (2nd ed.). O'Reilly Media.

O'Mahony, M. P., & Smyth, B. (2007). A recommender system for on-line course enrolment: An initial study. In Proceedings of the 2007 ACM Conference on Recommender Systems (pp. 133–136).

Parisi, A., Zhao, Y., & Fiedel, N. (2022). TALM: Tool augmented language models. arXiv preprint arXiv:2205.12255.

Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., ... & Scialom, T. (2023). Toolformer: Language models can teach themselves to use tools. arXiv preprint arXiv:2302.04761.

Slim, A., Heileman, G. L., Kozlick, J., & Abdallah, C. T. (2014). The complexity of university course scheduling: A graph-theoretic approach. arXiv preprint arXiv:1404.5137.


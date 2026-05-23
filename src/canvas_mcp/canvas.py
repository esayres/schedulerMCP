# this is where all canvas related code will go
# CANT DO THIS RIGHT NOW (canvas api is currently unavailable because of canvas hack :D)

#get_upcoming_assignments(course_id?)

#Returns:

#title
#due date
#course
#points
#status (if available)


#get_all_assignments()
#Returns:
#Aggregated across all courses.

#This becomes your foundation for everything else.

#Deadline Clustering (HIGH VALUE)
#detect_deadline_clusters(window_days=7)

#Finds:

#“bad weeks”
#assignment pileups
#exam collisions

#Output example:

#Week 5: 4 assignments due
#Week 9: midterm cluster

#This is one of your strongest “AI-feeling” features.


#analyze_course_workload(course_id)

#Estimates:

#weekly workload
#reading load
#assignment frequency
#difficulty score (heuristic at first)

#You can base this on:

#assignment frequency
#units
#lab hours (from your dataset)



#generate_study_plan(days_ahead=7)

#Takes:

#upcoming deadlines
#workload per course

#Outputs:

#daily breakdown (“do CS HW Tuesday 2–3h”)
#suggested pacing

#This is where MCP starts feeling like “AI assistant”






"""
5. Course Load Balancer
suggest_course_balance()

Uses:

workload estimates
deadlines
credits

Returns:

“This semester is heavy”
“Drop risk courses”
“balanced schedule suggestion”

Even simple heuristics look impressive here.

6. Deadline Conflict Detector
detect_overlapping_deadlines()

Finds:

same-day due items
same-week overload
exam + assignment collisions

This is SUPER useful for students.

7. Calendar Simulation (Advanced but powerful)
simulate_week(start_date)

Outputs:

day-by-day workload map
“stress graph” of the week

Even simple text output works.

8. Canvas Sync Layer (Background System)

Not a tool, but internal logic:

sync_canvas_data()
caching assignments locally
delta updates only

This is critical for performance and rate limits.


"""
"""
Quick examples of using ClickUp MCP with Claude or other AI assistants.

These are example prompts you can use once the MCP server is configured.
"""

# Example 1: Daily Standup Helper
daily_standup = """
Show me all tasks assigned to me that are in progress.
Then show me any urgent tasks in our team's space.
Finally, list tasks I completed yesterday.
"""

# Example 2: Sprint Planning
sprint_planning = """
1. Create a new list called "Sprint 23"
2. Move all high-priority backlog items to Sprint 23
3. Show me the team workload for Sprint 23
4. Create task chains for the main feature:
   - "Design new dashboard" (2h)
   - "Implement dashboard backend" (4h)
   - "Create dashboard frontend" (6h)
   - "Write dashboard tests" (3h)
   - "Deploy dashboard to staging" (1h)
"""

# Example 3: Bug Triage
bug_triage = """
1. Find all tasks tagged as "bug" in the last week
2. Group them by priority
3. Assign all unassigned critical bugs to the on-call engineer
4. Create a bug summary report
"""

# Example 4: Time Management
time_tracking = """
Show me time tracked by the team this week.
Log 3 hours on task "API Documentation" with note "Completed REST API docs".
What's my total time logged this month?
"""

# Example 5: Bulk Updates After Meeting
post_meeting = """
Based on our meeting decisions:
1. Move all "Design Review" tasks to "In Progress"
2. Update priority to High for tasks containing "customer"
3. Assign Sarah to all frontend tasks
4. Set due date to Friday for all tasks in "This Week" list
"""

# Example 6: Project Templates
new_project = """
Create a new project structure:
1. Create list "Customer Portal Feature"
2. Use the feature template to create:
   - "Customer Portal: User Stories"
   - "Customer Portal: Technical Design"
   - "Customer Portal: Implementation"
3. Create subtasks for Implementation:
   - Authentication system
   - User dashboard
   - Settings page
   - API integration
"""

# Example 7: Analytics & Reporting
weekly_report = """
Generate a weekly report:
1. Show task completion rate for the team
2. List top 5 contributors by tasks completed
3. Show average time to complete tasks by priority
4. Identify any blocked tasks older than 3 days
"""

print("🚀 ClickUp MCP Quick Start Examples")
print("=" * 50)
print("\nThese are example prompts you can use with Claude or other AI assistants")
print("once you have the ClickUp MCP server configured.\n")
print("Try copying any of these examples and pasting them into Claude!")
print("\nFor more examples, see: https://github.com/DiversioTeam/clickup-mcp")

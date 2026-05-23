"""
MCP Scheduling Tool - Course planning and schedule generation system.

This package provides comprehensive course scheduling functionality including:
- Course search and discovery
- Schedule conflict detection
- Prerequisite validation
- Workload estimation
- Multi-semester planning
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from . import database
from . import schueduling
from . import workload

__all__ = ["database", "schueduling", "workload"]

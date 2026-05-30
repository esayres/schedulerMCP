#!/usr/bin/env python3
"""
Unified Course Database Scraper

This script combines both web scrapers:
1. allCoursesScrapper - Gets course catalog (descriptions, prereqs, etc.)
2. schuedulerScrapper - Gets schedule data (sections, times, instructors)

Usage:
    python unified_scraper.py                    # Scrape current semester
    python unified_scraper.py --semester spring  # Scrape specific semester
    python unified_scraper.py --year 2026        # Scrape specific year
"""

import sys
import argparse
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from webscrapper import allCoursesScrapper as catalog_scraper
from webscrapper import schuedulerScrapper as schedule_scraper
from semesterSync import (
    get_current_semester,
    get_semester_info,
    merge_course_data,
    save_course_database,
    check_database_freshness
)


def scrape_catalog(semester_info: dict, parallel: bool = True) -> list:
    """
    Scrape course catalog data.
    
    Args:
        semester_info: Semester information dictionary
        parallel: Use parallel scraping for speed (default: True)
    
    Returns:
        List of course dictionaries
    """
    print(f"\n{'='*60}")
    print(f"STEP 1: Scraping Course Catalog")
    print(f"{'='*60}")
    print(f"Term: {semester_info['catalog_term']}")
    print(f"Semester: {semester_info['term_desc']}")
    print(f"Mode: {'PARALLEL (fast)' if parallel else 'SEQUENTIAL (slow)'}")
    
    # Get all departments
    print("\n[1/3] Fetching department list...")
    dept_data = catalog_scraper.fetch_all_disciplines(semester_info['catalog_term'])
    departments = dept_data['slugs']
    print(f"✓ Found {len(departments)} departments")
    
    # Scrape all courses
    print(f"\n[2/3] Scraping courses from {len(departments)} departments...")
    if parallel:
        print("Using parallel scraping (5 concurrent requests per department)")
    print("(This may take several minutes...)")
    
    all_courses = []
    for i, dept in enumerate(departments, 1):
        print(f"\n  [{i}/{len(departments)}] {dept}")
        try:
            if parallel:
                courses = catalog_scraper.crawl_department_parallel(
                    semester_info['catalog_term'],
                    dept,
                    max_workers=5  # 5 concurrent requests
                )
            else:
                courses = catalog_scraper.crawl_department(
                    semester_info['catalog_term'],
                    dept,
                    sleep=0.5
                )
            all_courses.extend(courses)
            print(f"    ✓ Found {len(courses)} courses")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue
    
    print(f"\n[3/3] Catalog scraping complete!")
    print(f"✓ Total courses scraped: {len(all_courses)}")
    
    return all_courses


def scrape_schedule(semester_info: dict) -> list:
    """
    Scrape schedule/section data with lab support.
    
    Args:
        semester_info: Semester information dictionary
    
    Returns:
        List of section dictionaries
    """
    print(f"\n{'='*60}")
    print(f"STEP 2: Scraping Schedule Data")
    print(f"{'='*60}")
    print(f"Term Code: {semester_info['schedule_term']}")
    print(f"Semester: {semester_info['term_desc']}")
    
    print("\n[1/2] Fetching schedule data...")
    
    # Import requests and BeautifulSoup here to avoid issues
    import requests
    from bs4 import BeautifulSoup
    
    url = "https://ssb.avc.edu/AVCPROD/pw_pub_sched.p_listthislist"
    
    payload = {
        "term": semester_info['schedule_term'],
        "term_desc": semester_info['term_desc'],
        "sel_day": "dummy",
        "sel_schd": "dummy",
        "sel_ism": "%",
        "sel_sess": "dummy",
        "sel_ptrm": "%",
        "begin_hh": "5",
        "begin_mi": "0",
        "begin_ap": "a",
        "end_hh": "11",
        "end_mi": "0",
        "end_ap": "p",
        "sel_subj": "%",
        "sel_camp": "%",
        "sel_instr": "%",
        "IsOpen": "N",
        "IsOnline": "N",
        "IsShrtTrm": "N",
        "isZtc": "N"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://ssb.avc.edu/AVCPROD/pw_pub_sched.p_Search"
    }
    
    try:
        session = requests.Session()
        session.get("https://ssb.avc.edu/AVCPROD/pw_pub_sched.p_Search")
        response = session.post(url, data=payload, headers=headers, timeout=30)
        
        print("[2/2] Parsing schedule data...")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Parse sections (FIXED to handle TBA, colspan, and lab rows)
        results = []
        current_course = None
        rows = soup.find_all("tr")
        
        i = 0
        while i < len(rows):
            row = rows[i]
            
            # Detect course header
            course_header = row.find("td", class_="crn_header")
            if course_header:
                current_course = course_header.get_text(strip=True)
                i += 1
                continue
            
            cells = row.find_all("td")
            
            # Skip header rows and empty rows
            if len(cells) < 10:
                i += 1
                continue
            
            # Check if this is a data row (has CRN link)
            crn_cell = cells[1] if len(cells) > 1 else None
            if not crn_cell:
                i += 1
                continue
            
            crn_link = crn_cell.find("a")
            if not crn_link:
                i += 1
                continue
            
            try:
                status = cells[0].get_text(strip=True)
                crn = crn_link.get_text(strip=True)
                section = cells[2].get_text(strip=True)
                credits = cells[3].get_text(strip=True)

                # Handle days - check for TBA or individual day cells
                days = []
                time_str = ""
                location = ""
                instructor = ""
                
                # Check if days are collapsed (TBA case)
                days_cell = cells[6] if len(cells) > 6 else None
                if days_cell and days_cell.get("colspan"):
                    # TBA case
                    days_text = days_cell.get_text(strip=True)
                    if days_text and days_text != "TBA":
                        days = [days_text]
                    
                    time_str = ""
                    location = cells[8].get_text(strip=True) if len(cells) > 8 else ""
                    instructor = cells[12].get_text(strip=True) if len(cells) > 12 else ""
                else:
                    # Normal case
                    for j in range(6, min(13, len(cells))):
                        d = cells[j].get_text(strip=True)
                        if d and d != "&nbsp;":
                            days.append(d)
                    
                    time_str = cells[13].get_text(strip=True) if len(cells) > 13 else ""
                    location = cells[15].get_text(strip=True) if len(cells) > 15 else ""
                    instructor = cells[19].get_text(strip=True) if len(cells) > 19 else ""
                
                # Create the main section entry
                section_data = {
                    "course": current_course,
                    "crn": crn,
                    "section": section,
                    "credits": credits,
                    "days": days,
                    "time": time_str,
                    "location": location,
                    "instructor": instructor,
                    "status": status
                }
                
                # Check if next row is a lab row (starts with colspan="6")
                if i + 1 < len(rows):
                    next_row = rows[i + 1]
                    next_cells = next_row.find_all("td")
                    
                    # Lab row detection: first cell has colspan="6" and is mostly empty
                    if (len(next_cells) > 0 and 
                        next_cells[0].get("colspan") == "6" and
                        not next_cells[0].find("a")):  # No CRN link
                        
                        # This is a lab row! Extract lab meeting time
                        lab_days = []
                        lab_time = ""
                        lab_location = ""
                        
                        # Days start at index 1 (after the colspan="6")
                        for j in range(1, min(8, len(next_cells))):
                            d = next_cells[j].get_text(strip=True)
                            if d and d != "&nbsp;":
                                lab_days.append(d)
                        
                        # Time is at index 8
                        lab_time = next_cells[8].get_text(strip=True) if len(next_cells) > 8 else ""
                        # Location is at index 10
                        lab_location = next_cells[10].get_text(strip=True) if len(next_cells) > 10 else ""
                        
                        # Add lab as additional meeting time
                        if not section_data.get("additional_times"):
                            section_data["additional_times"] = []
                        
                        section_data["additional_times"].append({
                            "days": lab_days,
                            "time": lab_time,
                            "location": lab_location,
                            "type": "lab"
                        })
                        
                        # Skip the lab row
                        i += 1
                
                results.append(section_data)
            except Exception:
                pass
            
            i += 1
        
        print(f"✓ Total sections scraped: {len(results)}")
        
        # Count sections with labs
        sections_with_labs = sum(1 for s in results if s.get("additional_times"))
        if sections_with_labs > 0:
            print(f"✓ Sections with lab times: {sections_with_labs}")
        
        return results
        
    except Exception as e:
        print(f"✗ Error scraping schedule: {e}")
        print("Continuing without schedule data...")
        return []


def main():
    """Main scraper entry point."""
    parser = argparse.ArgumentParser(
        description="Unified course database scraper for MCP Scheduling Tool"
    )
    parser.add_argument(
        "--semester",
        choices=["fall", "spring", "summer"],
        help="Semester to scrape (defaults to current)"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Year to scrape (defaults to current)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scrape even if database is fresh"
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Only scrape course catalog (skip schedule)"
    )
    parser.add_argument(
        "--schedule-only",
        action="store_true",
        help="Only scrape schedule (skip catalog)"
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel scraping (slower but safer)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent workers for parallel scraping (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Get semester info
    if args.semester or args.year:
        semester_info = get_semester_info(args.semester, args.year)
    else:
        semester_info = get_semester_info()
    
    print("="*60)
    print("MCP Scheduling Tool - Unified Course Database Scraper")
    print("="*60)
    print(f"\nTarget Semester: {semester_info['term_desc']}")
    print(f"Catalog Term: {semester_info['catalog_term']}")
    print(f"Schedule Term: {semester_info['schedule_term']}")
    print(f"Output File: {semester_info['filename']}")
    
    # Check if database is fresh
    if not args.force and check_database_freshness(semester_info):
        print(f"\n✓ Database for {semester_info['term_desc']} is already up to date!")
        print("Use --force to re-scrape anyway.")
        return 0
    
    # Scrape catalog
    catalog_courses = []
    if not args.schedule_only:
        try:
            parallel = not args.no_parallel
            catalog_courses = scrape_catalog(semester_info, parallel=parallel)
        except Exception as e:
            print(f"\n✗ Error scraping catalog: {e}")
            if args.catalog_only:
                return 1
    
    # Scrape schedule
    schedule_sections = []
    if not args.catalog_only:
        try:
            schedule_sections = scrape_schedule(semester_info)
        except Exception as e:
            print(f"\n✗ Error scraping schedule: {e}")
            if args.schedule_only:
                return 1
    
    # Merge data
    print(f"\n{'='*60}")
    print(f"STEP 3: Merging Data")
    print(f"{'='*60}")
    
    if catalog_courses and schedule_sections:
        print(f"Merging {len(catalog_courses)} courses with {len(schedule_sections)} sections...")
        merged_courses = merge_course_data(catalog_courses, schedule_sections)
        
        # Count courses with sections
        courses_with_sections = sum(1 for c in merged_courses if c.get("sections"))
        print(f"✓ {courses_with_sections} courses have section data")
    elif catalog_courses:
        print("Using catalog data only (no schedule data available)")
        merged_courses = catalog_courses
    elif schedule_sections:
        print("Using schedule data only (no catalog data available)")
        merged_courses = []
    else:
        print("✗ No data scraped!")
        return 1
    
    # Save database
    print(f"\n{'='*60}")
    print(f"STEP 4: Saving Database")
    print(f"{'='*60}")
    
    filepath = save_course_database(merged_courses, semester_info)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE!")
    print(f"{'='*60}")
    print(f"✓ Semester: {semester_info['term_desc']}")
    print(f"✓ Total Courses: {len(merged_courses)}")
    if schedule_sections:
        courses_with_sections = sum(1 for c in merged_courses if c.get("sections"))
        print(f"✓ Courses with Sections: {courses_with_sections}")
        print(f"✓ Total Sections: {len(schedule_sections)}")
    print(f"✓ Saved to: {filepath}")
    print(f"\nYou can now use the MCP server with this data!")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

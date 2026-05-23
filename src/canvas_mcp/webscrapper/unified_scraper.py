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


def scrape_catalog(semester_info: dict) -> list:
    """
    Scrape course catalog data.
    
    Args:
        semester_info: Semester information dictionary
    
    Returns:
        List of course dictionaries
    """
    print(f"\n{'='*60}")
    print(f"STEP 1: Scraping Course Catalog")
    print(f"{'='*60}")
    print(f"Term: {semester_info['catalog_term']}")
    print(f"Semester: {semester_info['term_desc']}")
    
    # Get all departments
    print("\n[1/3] Fetching department list...")
    dept_data = catalog_scraper.fetch_all_disciplines(semester_info['catalog_term'])
    departments = dept_data['slugs']
    print(f"✓ Found {len(departments)} departments")
    
    # Scrape all courses
    print(f"\n[2/3] Scraping courses from {len(departments)} departments...")
    print("(This may take several minutes...)")
    
    all_courses = []
    for i, dept in enumerate(departments, 1):
        print(f"\n  [{i}/{len(departments)}] {dept}")
        try:
            courses = catalog_scraper.crawl_department(
                semester_info['catalog_term'],
                dept,
                sleep=0.5  # Be nice to the server
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
    Scrape schedule/section data.
    
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
        
        # Parse sections
        results = []
        current_course = None
        rows = soup.find_all("tr")
        
        for row in rows:
            # Detect course header
            course_header = row.find("td", class_="crn_header")
            if course_header:
                current_course = course_header.get_text(strip=True)
                continue
            
            cells = row.find_all("td")
            
            # Section rows have many columns
            if len(cells) >= 15:
                try:
                    status = cells[0].get_text(strip=True)
                    crn = cells[1].get_text(strip=True)
                    section = cells[2].get_text(strip=True)
                    credits = cells[3].get_text(strip=True)
                    
                    # Days (M T W R F etc.)
                    days = []
                    for i in range(6, 13):
                        d = cells[i].get_text(strip=True)
                        if d:
                            days.append(d)
                    
                    time_str = cells[13].get_text(strip=True)
                    location = cells[15].get_text(strip=True)
                    instructor = cells[19].get_text(strip=True)
                    
                    results.append({
                        "course": current_course,
                        "crn": crn,
                        "section": section,
                        "credits": credits,
                        "days": days,
                        "time": time_str,
                        "location": location,
                        "instructor": instructor,
                        "status": status
                    })
                except Exception:
                    pass
        
        print(f"✓ Total sections scraped: {len(results)}")
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
            catalog_courses = scrape_catalog(semester_info)
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

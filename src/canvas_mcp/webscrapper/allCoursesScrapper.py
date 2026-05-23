"""
AVC eLumen Catalog Scraper (MCP ingestion helper)

Goal:
- Crawl department pages (HTML)
- Extract course links
- Fetch course detail JSON/HTML endpoints
- Normalize into structured dataset

This is designed to be used inside your MCP ingestion tool:
build_course_database(term)
"""

# REFACTOR LATER

import requests
from bs4 import BeautifulSoup
#from urllib.parse import urljoin
import re
import time
import json

BASE = "https://api-prod.elumenapp.com/catalog/sites/publish/content/"
TENANT = "avc.elumenapp.com"
SESSION = requests.Session()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (MCP Scraper)"
}

# ----------------------------
# Core HTTP helpers
# ----------------------------

def fetch(url: str) -> str:
    """Fetch raw HTML/text."""
    resp = SESSION.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text


def fetch_json_like(url: str) -> dict:
    """Some endpoints return JSON-like HTML responses."""
    resp = SESSION.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}

# ----------------------------
# Step 1: parse department page
# ----------------------------

def parse_department_courses(html: str):
    """Extract course slugs + titles from department HTML."""
    soup = BeautifulSoup(html, "html.parser")

    courses = []

    for a in soup.select("a.navitem"):
        href = a.get("href", "")
        text = a.get_text(strip=True)

        # extract course code from URL
        # e.g. 2025-26/course/fren101
        if "course" in href:
            parts = href.split("/")
            course_id = parts[-1] if parts else None

            courses.append({
                "course_id": course_id,
                "title": text,
                "href": href
            })

    return courses


def parse_description(description: str):
    """Extract prereqs/coreqs/advisories and clean description."""

    prereqs = []
    coreqs = []
    advisory = []
    limitation = []

    # Match helper
    def extract_courses(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        raw = match.group(1)

        # clean html
        raw = re.sub(r"<br\s*/?>", " ", raw)
        raw = re.sub(r"\s+", " ", raw)

        results = []

        # Split logical OR groups
        parts = re.split(r"\s+or\s+", raw, flags=re.IGNORECASE)

        for part in parts:

            # capture:
            # ENGL C1000 (ENGL 101)
            alias_match = re.search(
                r"([A-Z]{2,5}\s?[A-Z]?\d{3,4}[A-Z]?)\s*\(([^)]+)\)",
                part
            )

            if alias_match:
                main = alias_match.group(1).strip()

                aliases = re.findall(
                    r"[A-Z]{2,5}\s?[A-Z]?\d{3,4}[A-Z]?",
                    alias_match.group(2)
                )

                grouped = [main] + aliases

                results.append({"or": grouped})

            else:
                courses = re.findall(
                    r"[A-Z]{2,5}\s?[A-Z]?\d{3,4}[A-Z]?",
                    part
                )

                if len(courses) == 1:
                    results.append(courses[0])

                elif courses:
                    results.append(courses)

        return results


    def extract_text(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if not match:
            return []

        raw = match.group(1)

        # clean html
        raw = re.sub(r"<br\s*/?>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()

        return [raw]

    prereqs = extract_courses(r"Prerequisites?:\s*(.*?)(?=Corequisites?:|Advisory?:|Limitation on Enrollment?:|$)",description)
    coreqs = extract_courses(r"Corequisite[s]?:\s*(.*?)(?=Prerequisite[s]?:|Advisory?:|Limitation on Enrollment?:|$)",description)
    advisory = extract_courses(r"Advisory?:\s*(.*?)(?=Prerequisites?:|Corequisites?:|Limitation on Enrollment?:|$)",description)
    limitation = extract_text(r"Limitation on Enrollment?:\s*(.*?)(?=Prerequisites?:|Corequisites?:|Advisory?:|$)",description)

    # Remove metadata sentences
    patterns_to_remove = [
        r"Prerequisites?:\s*[^\.]+\.",
        r"Corequisites?:\s*[^\.]+\.",
        r"Advisory?:\s*[^\.]+\.",
        r"Limitation on Enrollment?:\s*[^\.]+\."
    ]

    for pattern in patterns_to_remove:
        description = re.sub(pattern, "", description, flags=re.IGNORECASE)

    # -------------------------
    # CLEANUP PHASE
    # -------------------------

    # probly bad but it works for now
    
    # Remove repeated blank lines
    description = re.sub(r"\n\s*\n+", "\n", description)

    # Remove lines that are ONLY periods/spaces
    description = re.sub(r"^\s*\.+\s*$", "", description, flags=re.MULTILINE)

    # Collapse multiple periods
    description = re.sub(r"\.{2,}", ".", description)

    # Normalize whitespace
    description = re.sub(r"[ \t]+", " ", description)

    # Final strip
    description = description.strip()

    return description, prereqs, coreqs, advisory, limitation


# ----------------------------
# Step 2: fetch course details
# ----------------------------

def fetch_course_detail(term: str, course_id: str):
    """Fetch and parse structured course page."""

    url = f"{BASE}{term},course,{course_id}?tenant={TENANT}"

    data = fetch_json_like(url)

    # ---- 1. Extract HTML safely ----
    html = None

    if isinstance(data, dict):
        html = data.get("raw") or data.get("html")
    elif isinstance(data, str):
        html = data
    else:
        raise ValueError("Unexpected response format")

    if not html:
        raise ValueError("No HTML found in response")

    # ---- 2. Parse HTML ----
    soup = BeautifulSoup(html, "html.parser")

    # ---- 3. Extract fields ----
    header = soup.find("header")
    title = None
    units = None
    course_title = None
    honors = False

    if header:
        h2 = header.find("h2")
        h3 = header.find("h3")
        p = header.find("p")

        title = h2.get_text(strip=True) if h2 else None
        course_title = h3.get_text(strip=True) if h3 else None
        units = p.get_text(strip=True) if p else None

    description_tag = soup.select_one(".introtext")
    description = str(description_tag)

    description = re.sub(r"<br\s*/?>", "\n", description)

    description = BeautifulSoup(description, "html.parser").get_text(" ")

    description = re.sub(r"\s+", " ", description).strip()


    # need to parse description for prereqs and co-reqs
    # return description, prereqs, coreqs, advisory, limitation
    description, prereqs, coreqs, advisory, limitation = parse_description(description)
    # ---- Units & Hours ----
    def get_label_value(label):
        el = soup.find("h5", string=lambda x: x and label in x)
        if not el:
            return None
        parent = el.find_next("div")
        return parent.get_text(strip=True) if parent else None

    course_title = course_title[:-1] # remvoes the : at the end
    if course_title[-1].lower() == "h": # checks if honors course
        honors = True
    

    result = {
        "course_id": course_id,
        "title": title,
        "course_title": course_title,
        "honors": honors,
        "units": units,
        "description": description,
        "prereqs": prereqs,
        "coreqs": coreqs,
        "advisory": advisory,
        "limitation": limitation,

        "min_units": get_label_value("Minimum Credit Units"),
        "max_units": get_label_value("Maximum Credit Units"),
        "contact_hours": get_label_value("Total Course In-Class"),
        "out_of_class_hours": get_label_value("Total Course Out-of-Class Hours"),
        "lecture_hours": get_label_value("Total Course Lecture Hours"),
        "lab_hours": get_label_value("Total Course Lab Hours"),
    }

    return result

# ----------------------------
# all department Scrape
# ----------------------------
def fetch_all_disciplines(term: str):
    """Fetch list of all departments (disciplines)."""

    url = f"{BASE}{term},allldisciplines?tenant={TENANT}"

    data = fetch_json_like(url)

    # ---- Extract HTML safely ----
    html = None
    if isinstance(data, dict):
        html = data.get("raw") or data.get("html")
    elif isinstance(data, str):
        html = data
    else:
        raise ValueError("Unexpected response format")

    if not html:
        raise ValueError("No HTML found in response")

    soup = BeautifulSoup(html, "html.parser")

    departments = []
    departmentSlug = []

    for a in soup.select("a.navitem"):
        name_tag = a.select_one(".navitem-x-text")
        name = name_tag.get_text(strip=True) if name_tag else None

        # href like: 2025-26/department/accounting
        href = a.get("href", "")
        slug = href.split("/")[-1] if href else None

        # extract real API URL from onclick
        onclick = a.get("onclick", "")
        match = re.search(r"loadContent\('([^']+)'", onclick)
        api_url = match.group(1) if match else None

        departments.append({
            "name": name,
            "slug": slug,
            "href": href,
            #"api_url": api_url
        })
        departmentSlug.append(slug)

    return {
        "term": term,
        "count": len(departments),
        "departments": departments,
        "slugs": departmentSlug
    }

# ----------------------------
# Step 3: extract department page
# ----------------------------

def fetch_department(term: str, dept: str):
    """Fetch department page (HTML)."""

    url = f"{BASE}{term},department,{dept}?tenant={TENANT}"
    return fetch(url)

# ----------------------------
# Step 4: full crawl
# ----------------------------

def crawl_department(term: str, dept: str, sleep=0.5):
    """Crawl full department -> courses -> course details."""

    print(f"[+] Crawling department: {dept}")

    html = fetch_department(term, dept)
    courses = parse_department_courses(html)

    results = []

    for c in courses:
        course_id = c["course_id"]

        print(f"    [-] Fetching {course_id}")

        try:
            detail = fetch_course_detail(term, course_id)
            detail["department"] = dept
            detail["label"] = c["title"]

            results.append(detail)

        except Exception as e:
            print(f"    [!] Error: {course_id} -> {e}")

        time.sleep(sleep)  # rate limit safety

    return results

# ----------------------------
# Step 5: build full dataset
# ----------------------------

def build_course_database(term: str, departments: list):
    """Build full dataset for MCP."""

    all_courses = []

    for dept in departments:
        data = crawl_department(term, dept)
        all_courses.extend(data)

    return all_courses

# ----------------------------
# Example usage
# ----------------------------

if __name__ == "__main__":
    TERM = "2025-26"

    # you would get this from allldisciplines endpoint
    #departments = ["french", "computer-science"]
    departments = fetch_all_disciplines(TERM)['slugs']

    dataset = build_course_database(TERM, departments)

    with open("courses.json", "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Saved {len(dataset)} courses")

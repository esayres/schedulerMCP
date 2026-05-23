import requests
from bs4 import BeautifulSoup

# SO COURSES with several times (like physics labs and class) # dont link together in the same class
# also CS:230 doesnt appear for some reason?


# --- STEP 1: Fetch (same as before) ---
url = "https://ssb.avc.edu/AVCPROD/pw_pub_sched.p_listthislist"

# techincally i should figure out how exactly to get the exact term I want (term and DESC) somewhere i can keep scrapping
# i also need a main.py scrapper that uses both scrappers to get a acruate database

payload = {
    "term": "202630",
    "term_desc": "Spring 2026",
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

session = requests.Session()
session.get("https://ssb.avc.edu/AVCPROD/pw_pub_sched.p_Search")
response = session.post(url, data=payload, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")

# --- STEP 2: Parse ---
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
    
    # Section rows have many columns (usually ~20+)
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

            time = cells[13].get_text(strip=True)
            location = cells[15].get_text(strip=True)
            instructor = cells[19].get_text(strip=True)

            results.append({
                "course": current_course,
                "crn": crn,
                "section": section,
                "credits": credits,
                "days": days,
                "time": time,
                "location": location,
                "instructor": instructor
            })

        except Exception:
            pass

# --- STEP 3: Test output ---
for r in results[:5]:
    print(r)


# so courses with

print("Total sections:", len(results))
for i in results:
    idx = i["course"].find("PHYS")
    if idx != -1:
        print(i)
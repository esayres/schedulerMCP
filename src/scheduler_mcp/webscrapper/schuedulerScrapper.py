import requests
from bs4 import BeautifulSoup

# --- STEP 1: Fetch (same as before) ---
url = "https://ssb.avc.edu/AVCPROD/pw_pub_sched.p_listthislist"

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

# --- STEP 2: Parse (FIXED to handle TBA, colspan, and lab rows) ---
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

        # Create section entry
        section_data = {
            "course": current_course,
            "crn": crn,
            "section": section,
            "credits": credits,
            "days": days,
            "time": time_str,
            "location": location,
            "instructor": instructor
        }
        
        # Check if next row is a lab row (starts with colspan="6")
        if i + 1 < len(rows):
            next_row = rows[i + 1]
            next_cells = next_row.find_all("td")
            
            # Lab row detection: first cell has colspan="6" and no CRN link
            if (len(next_cells) > 0 and 
                next_cells[0].get("colspan") == "6" and
                not next_cells[0].find("a")):
                
                # This is a lab row!
                lab_days = []
                lab_time = ""
                lab_location = ""
                
                # Days start at index 1 (after colspan="6")
                for j in range(1, min(8, len(next_cells))):
                    d = next_cells[j].get_text(strip=True)
                    if d and d != "&nbsp;":
                        lab_days.append(d)
                
                # Time at index 8, Location at index 10
                lab_time = next_cells[8].get_text(strip=True) if len(next_cells) > 8 else ""
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

    except Exception as e:
        # Debug: print which row failed
        # print(f"Failed to parse row: {e}")
        pass
    
    i += 1


# Statistics
print("\nTotal sections:", len(results))

# Count sections with labs
sections_with_labs = sum(1 for s in results if s.get("additional_times"))
if sections_with_labs > 0:
    print(f"Sections with lab times: {sections_with_labs}")

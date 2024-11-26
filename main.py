from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests, time, os


def get_html(dept, course_num):
    URL = f"https://app.testudo.umd.edu/soc/search?courseId={dept}{course_num}&sectionId=&termId=202501&_openSectionsOnly=on&creditCompare=%3E%3D&credits=0.0&courseLevelFilter=ALL&instructor=&_facetoface=on&_blended=on&_online=on&courseStartCompare=&courseStartHour=&courseStartMin=&courseStartAM=&courseEndHour=&courseEndMin=&courseEndAM=&teachingCenter=ALL&_classDay1=on&_classDay2=on&_classDay3=on&_classDay4=on&_classDay5=on"
    
    r = requests.get(URL)
    
    if r.status_code == 200:
        return r.text
    else:
        print("Error ", r.status_code)
        return -1
    

def get_course_info(soup):
    course_data = []
    section_info = soup.findAll("div", "section-info-container")

    for section in section_info:
        section_number = section.find("div", class_="section-id-container").find("span", class_="section-id").text.strip()
        instructor_name_tag = section.find("div", class_="section-instructors-container").find("span", class_="section-instructor")
        instructor_name = instructor_name_tag.text.strip()
        total_seats = section.find("span", class_="total-seats-count").text.strip()
        open_seats = section.find("span", class_="open-seats-count").text.strip()
        waitlist_count = section.find("span", class_="waitlist-count").text.strip()

        section_data = {
            "section_number": section_number,
            "instructor_name": instructor_name,
            "total_seats": total_seats,
            "open_seats": open_seats,
            "waitlist_count": waitlist_count,
        }

        course_data.append(section_data)
    
    return course_data


def post_to_discord(message, is_course_msg=True):
    load_dotenv()
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    if is_course_msg:
        course_data = format_course_data(message)
        
        payload = {
            "content": course_data.strip()
        }

        headers = {"Content-Type": "application/json"}
    else:
        payload = {
            "content": message.strip()
        }

        headers = {"Content-Type": "application/json"}

    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")


def format_course_data(course_data):
    message_content = ""

    for section in course_data:
        message_content += (
            f"**Section Number:** {section['section_number']}\n"
            f"**Instructor Name:** {section['instructor_name']}\n"
            f"**Total Seats:** {section['total_seats']}\n"
            f"**Open Seats:** {section['open_seats']}\n"
            f"**Waitlist Count:** {section['waitlist_count']}\n"
            f"-------------------------\n"
        )
    
    return message_content


def get_desired_course():
    dept = input("Enter the department (e.g. CMSC): ")
    course_num = input("Enter the course number (e.g. 351): ")

    return dept, course_num


def get_target_sections():
    target_sections = input("Enter the target sections (e.g. 0101, 0201, 0301): ").split(",")

    return target_sections


def send_initial_message(dept, course_num, target_sections):
    initial_message = f"Program started. Checking for open seats every 15 minutes in {dept}{course_num} - sections: {', '.join(target_sections)}.\nA message will be sent only if the monitored sections have open seats."
    post_to_discord(initial_message, is_course_msg=False)


def main():
    dept, course_num = get_desired_course()
    target_sections = get_target_sections()

    send_initial_message(dept, course_num, target_sections)

    while True:
        html = get_html(dept, course_num)

        if (html == -1): continue

        soup = BeautifulSoup(html, "html.parser")
        course_data = get_course_info(soup)

        sections_with_open_seats = [section for section in course_data if (int(section["open_seats"]) > 0 and section["section_number"] in target_sections)]
        
        if sections_with_open_seats:
            post_to_discord(sections_with_open_seats)

        time.sleep(60 * 10) # 10 minutes


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            continue

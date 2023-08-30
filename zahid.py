# pip install pandas requests beautifulsoup4 openpyxl

import pandas as pd
import requests
import re
import random
import json
from bs4 import BeautifulSoup
import traceback

# excel_file = 'Website Links.xlsx'
excel_file = 'Website Links Test.xlsx'
df = pd.read_excel(excel_file)
urls = df['project_url'].tolist()


# proxy_list = [
#     "http://50.218.57.71:80",
#     "http://68.188.59.198:80",
#     "http://20.219.178.121:3129",
#     "http://20.210.113.32:80",
#     "http://213.33.126.130:80",
#     "http://213.157.6.50:80",
# ]


def scrape_data_with_proxy(url):
    # proxy = random.choice(proxy_list)
    # proxies = {"http": proxy, "https": proxy}
    proxies = {"http": "http://137.184.232.148:80", "https": "http://82.102.31.242:8443"}

    try:
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        # }

        # response = requests.get(url, headers=headers, proxies=proxies)
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Project ID
            xid_pattern = r'xid":\s*"(\d+)"'
            match = re.search(xid_pattern, str(soup))
            if match:
                project_id = match.group(1)
            else:
                project_id = url.split("-")[-1][1:]

            # Project Name
            project_name = soup.find('div', {'id': 'projectNameTab'}).text

            # Latitude, Longitude, Sub Location and City
            script_tags = soup.find_all('script', {'type': 'application/ld+json'})

            latitude = None
            longitude = None
            sub_location = None
            city_name = None

            for script_tag in script_tags:
                json_data = json.loads(script_tag.string)
                if "@type" in json_data and json_data["@type"] == "Place" and "geo" in json_data:
                    latitude = json_data["geo"].get("latitude")
                    longitude = json_data["geo"].get("longitude")
                elif "@type" in json_data and json_data["@type"] == "Residence" and "address" in json_data:
                    sub_location = json_data["address"].get("addressLocality")
                    city_name = json_data["address"].get("addressRegion")

            # Project Description, Landmarks, State and REGA
            script_tags = soup.find_all('script')
            pattern = re.compile(r'window.__initialData__\s*=\s*({.*?});', re.DOTALL)

            project_description = None
            landmarks = None
            state = None
            rega = None

            for script_tag in script_tags:
                if script_tag.string is not None:
                    match = pattern.search(script_tag.string)
                    if match:
                        json_data_str = match.group(1)

                        data = json.loads(json_data_str)

                        landmarks = data.get("projectDetailState", {}).get("nearbyLandMarks", {})
                        state = data.get("projectDetailState", {}).get('pageData', {}).get('basicDetails', {}).get(
                            'location', {}).get("stateName")
                        rega = data.get("projectDetailState", {}).get('pageData', {}).get('components', {}).get(
                            'summaryLayer', {}).get('rera', {}).get('registrationNumber', {})

                        # Project Description
                        description = data.get("projectDetailState", {}).get('pageData', {}).get('components', {}).get(
                            'moreAboutProject', {}).get('description', {})
                        description_soup = BeautifulSoup(description, 'html.parser')
                        project_description = description_soup.get_text()
                        break
            else:
                print("Script tag with window.__initialData__ not found.")

            # Construction Status
            construction_status = None
            under_construction_element = soup.find(class_="ConstructionStatus__phaseStatus")
            if under_construction_element:
                construction_status = under_construction_element.get_text()

            # Project Completion Date
            completion_date = None
            completion_tag = soup.find(class_='ConstructionStatus__phaseStatusSubtitle')
            if completion_tag:
                completion_text = completion_tag.get_text()
                completion_date = completion_text.split('Completion in ')[1]
            else:
                print("Completion tag not found.")

            # Project Rating
            rating = None
            rating_area = soup.find(class_="review__ratingArea")
            if rating_area:
                rating_element = rating_area.find(class_="display_l_semiBold")
                if rating_element:
                    rating_text = rating_element.get_text()
                    rating = f"{rating_text}/5"
                else:
                    print("Rating element not found within review__ratingArea.")
            else:
                print("review__ratingArea not found in the HTML.")

            # Project FAQs
            faq_dict = {}
            faq_div = soup.find('div', id='faqs')
            if faq_div:
                faq_blocks = faq_div.find_all('div', class_='Faq__questionBlock')
                for faq_block in faq_blocks:
                    question = faq_block.find('div', class_='list_header_semiBold').text.strip()
                    answer = faq_block.find('div', class_='caption_strong_large').text.strip()
                    faq_dict[question] = answer
            else:
                print("FAQs not found.")

            # Project Advantages
            body_med_divs = soup.find_all('div', class_='body_med')
            advantages = list()
            for div in body_med_divs:
                data = div.get_text(strip=True)
                advantages.append(data)

            project_data = {
                'project_id': project_id,
                'project_name': project_name,
                'project_description': project_description,
                'landmarks': landmarks,
                'faq': faq_dict,
                'latitude': latitude,
                'longitude': longitude,
                'sub_location': sub_location,
                'city_name': city_name,
                'state': state,
                # 'low_cost_text': low_cost_text,
                # 'high_cost_text': high_cost_text,
                'project_url': url,
                "status": construction_status,
                'rega': rega,
                'completion_date': completion_date,
                'rating': rating,
                'advantages': advantages
                # 'amenities': amenities,
                # 'media': media,
            }

            return project_data
        else:
            print(f"Error accessing URL: {url}")
            return None
    except Exception as e:
        error_msg = str(e)
        traceback_info = traceback.format_exc()
        print(f"Error: {error_msg}\nTraceback: {traceback_info}")
        print(f"Error: {e}")
        return None


scraped_data = []
for url in urls:
    project_data = scrape_data_with_proxy(url)
    if project_data:
        scraped_data.append(project_data)

unique_project_data = {data['project_id']: data for data in scraped_data}
json_output = json.dumps(unique_project_data, indent=4)

with open('Zahid_data.json', 'w') as json_file:
    json_file.write(json_output)

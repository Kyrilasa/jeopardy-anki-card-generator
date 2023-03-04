from datetime import datetime
from bs4 import BeautifulSoup
import requests
import re

pattern = r'\d{4}-\d{2}-\d{2}'
clue_pattern = r'clue_(J|DJ)(_\d+_\d+)*'
solution_pattern = r"correct_response&quot;&gt;([^']*)&lt;/em&gt;"


def get_game_urls_before_date(date_threshold):
    # Fetch the HTML content of the link
    link = "http://j-archive.com/listseasons.php"
    response = requests.get(link)
    html_content = response.content
    stop_looping = False

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all the links to the individual seasons
    season_links = soup.find_all('a', href=True)

    # Extract the URLs and season names from the links
    season_urls = []
    season_names = []
    for link in season_links:
        if link.text.startswith('Season '):
            season_urls.append(link['href'])
            season_names.append(link.text)

    # Print the URLs and names of the seasons
    game_urls = []
    for url, _ in zip(season_urls, season_names):
        response = requests.get(f"http://j-archive.com/{url}")
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        episode_links = soup.find_all('a', href=True)

        for link in episode_links:
            if link.text.startswith("#"):
                # print(link.text)
                match = re.search(pattern, link.text)
                date_string = match.group(0)

                date = datetime.strptime(date_string, '%Y-%m-%d')

                # Define the arbitrary date for comparison
                arbitrary_date = datetime.strptime(
                    date_threshold, '%Y-%m-%d')
                if date < arbitrary_date:
                    stop_looping = True
                    break
                # print(link['href'])
                game_urls.append(link['href'])
        if stop_looping:
            break
    return game_urls


def prettify_round_identifier(round_id):
    if round_id == "jeopardy_round":
        return "Jeopardy"
    elif round_id == "double_jeopardy_round":
        return "Double Jeopardy"
    else:
        return "Final Jeopardy"


def gather_show_round_data(soup, show_object, round_id):
    round_data = soup.find_all('table', {'class': round_id})
    is_final = True if round_id == 'final_round' else False
    if len(round_data) > 0:
        if is_final:
            round_object = {
                'round_id': prettify_round_identifier(round_data[0].parent['id']), 'questions': []}
            categories = [category.text for category in round_data[0].find_all(
                'td', {'class': "category_name"})]
            round_object['questions'].append(
                gather_clue_and_answer(round_data[0], categories, is_final))

            show_object['rounds'].append(round_object)
        else:
            for round_div in round_data:
                round_object = {
                    'round_id': prettify_round_identifier(round_div.parent['id']), 'questions': []}
                clues = [td for td in round_div.find_all(
                    'td', {'class': 'clue'})]
                categories = [category.text for category in round_div.find_all(
                    'td', {'class': "category_name"})]
                for clue in clues:
                    if (clue_and_answer := gather_clue_and_answer(clue, categories, is_final)) is not None:
                        round_object['questions'].append(clue_and_answer
                                                         )
                show_object['rounds'].append(round_object)


def gather_clue_and_answer(clue, categories, is_final=False):
    if not is_final:
        return gather_clue_and_answer_from_simple_round(clue, categories)
    else:
        return gather_clue_and_answer_from_final_round(clue, categories)


def gather_clue_and_answer_from_final_round(clue, categories):
    onmouseover_javascript_function = clue.find(
        'div', {'onmouseover': True})['onmouseover']
    return _scrape_clue_and_answer(clue, categories, onmouseover_javascript_function)


def gather_clue_and_answer_from_simple_round(clue, categories):
    clue_header = clue.find('table', {'class': "clue_header"})
    if clue_header is None:
        return
    onmouseover_javascript_function = clue_header.parent['onmouseover']
    return _scrape_clue_and_answer(clue, categories, onmouseover_javascript_function)


def _scrape_clue_and_answer(clue, categories, javascript_function):
    pattern = r'<em class="correct_response">.+</em>'
    match = re.search(pattern, javascript_function)
    third_param = match.group(0)
    solution = third_param.replace(
        '<em class="correct_response">', '').replace("</em>", '')
    question = clue.find('td', {'class': "clue_text"})
    question_text = question.text
    pattern = r'<.*?>'
    question_text = re.sub(pattern, '', question_text)
    solution = re.sub(pattern, '', solution)

    category_idx = int(question['id'][-1]
                       ) if question['id'][-1].isdigit() else 0
    clue_value = clue.find('td', {'class', "clue_value"})
    dd_clue_value = clue.find('td', {'class', "clue_value_daily_double"})
    question_value = dd_clue_value if clue_value is None else clue_value
    return {
        'prompt': question_text,
        'answer': solution,
        'category': categories[category_idx],
        'value': question_value.text if question_value is not None else 'final'}


def scrape(game_urls):
    for url in game_urls:
        response = requests.get(url)
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        game_info = soup.find('title').text.split(" ")[-1]
        show_object = {'air_date': game_info, 'rounds': []}
        gather_show_round_data(soup, show_object, 'round')
        gather_show_round_data(soup, show_object, 'final_round')
        yield show_object


if __name__ == "__main__":
    for show_object in scrape(get_game_urls_before_date("2023-03-01")):
        print(show_object)

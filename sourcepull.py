import requests
from bs4 import BeautifulSoup
import re
import urllib3
from num2words import num2words
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# список разделов, на которых прекращается чтение файла, т.к. далее идет информация, не несущая смысловой нагрузки
stop_sections = [
    'In popular media', 'See also', 'Notes and references',
    'Bibliography', 'Primary sources', 'External links',
    'References', 'Cited literature', 'Notes', 'Further reading'
]

# список английских предлогов для удаления, так как они не несут особой смысловой нагрузки, но присутствуют во многих предложениях
prepositions = [
    'about', 'above', 'across', 'after', 'against', 'along', 'among', 'around', 'at',
    'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'but',
    'by', 'concerning', 'considering', 'despite', 'down', 'during', 'except',
    'for', 'from', 'in', 'inside', 'into', 'like', 'near', 'of', 'off', 'on',
    'onto', 'out', 'outside', 'over', 'past', 'regarding', 'since', 'through',
    'throughout', 'to', 'toward', 'under', 'underneath', 'until', 'up', 'upon',
    'with', 'within', 'without', 'atop', 'amid', 'amidst', 'versus', 'per', 'via'
]


# преобразование всех чисел в строке в слова
def num_to_words(text):
    def replace(match):
        num = match.group(0)
        try:
            return num2words(int(num), lang='en')
        except:
            return num

    return re.sub(r'\b\d+\b', replace, text)


# оставляет только буквы и точки, удаляет предлоги
def clean_sentence(sentence):
    sentence = re.sub(r'[^a-zA-Z.\-—\s]', '', sentence)

    words = sentence.split()
    filtered_words = []

    for word in words:
        # чистое слово для проверки условий (без точек и тире)
        clean_word = re.sub(r'[.\-—]', '', word).lower()

        # условие: длина >= 4 и это не предлог
        if len(clean_word) >= 4 and clean_word not in prepositions:
            filtered_words.append(word)
        # сохраняем знаки препинания, если они идут отдельно
        elif word in ['.', '-', '—']:
            filtered_words.append(word)

    return " ".join(filtered_words)


def export_wiki(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(url, headers=headers, verify=False, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # обработка названия файла (цифры -> слова)
    title_raw = soup.find('h1').get_text().strip()
    file_prefix = num_to_words(title_raw)
    filename = re.sub(r'[\\/*?:"<>|]', '', file_prefix) + ".txt"

    content = soup.select_one('.mw-parser-output')

    processed_lines = []
    last_year = "unknown year"

    # проходим по параграфам, заголовкам и спискам
    for element in content.find_all(['p', 'h2', 'h3', 'li']):
        text = element.get_text().strip()

        # если встречается стоп слово- завершаем обработку страницы
        if any(stop_word in text for stop_word in stop_sections):
            break

        # удаляем сноски
        text = re.sub(r'\[.*?\]', '', text)
        if not text: continue

        # делим на предложения по точкам
        sentences = re.split(r'(?<=[.])\s+', text)

        for s in sentences:
            s = s.strip()
            if not s: continue

            # обновляем "текущий год", если он найден (4 цифры)
            found_years = re.findall(r'\b(\d{4})\b', s)
            if found_years:
                last_year = num2words(int(found_years[-1]), lang='en')

            # если год не найден, пропускаем строку - это вступительные слова до каких-либо важных событий
            if last_year == "unknown year":
                continue

            # фильтруем само предложение
            cleaned_s = clean_sentence(s)

            # удаление оставшихся лишних символов, различные вариации записи данных
            if cleaned_s and cleaned_s != ".":
                # заголовок + год + событие:
                line = f"{file_prefix.replace('-', '')}{last_year.replace('-' or 'and', '')}{cleaned_s.replace('-', '')}"
                # заголовок + событие:
                # line = f"{file_prefix.replace('-', '')}{cleaned_s.replace('-', '')}"
                # год + само событие:
                # line = f"{last_year.replace('-' or 'and', '')}{cleaned_s.replace('-', '')}"
                # только событие:
                # line = f"{cleaned_s.replace('-', '')}"
                processed_lines.append(line)

    # запись полученной статьи в соответствующий файл
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(processed_lines))


# функция, объединяющая все статьи в 1 датасет
def merge():
    files = [f for f in os.listdir('.') if f.endswith('.txt') and f != "dataset.txt" and f != 'LINKS.txt']
    with open("dataset.txt", "w", encoding="utf-8") as outfile:
        for filename in files:
            with open(filename, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())
                outfile.write("\n")

# запуск итоговой программы
if __name__ == "__main__":
    f = open("LINKS.txt")
    for url in f:
        url = url[0:len(url) - 1]
        export_wiki(url)
    merge()


# Подсчет параметров датасета
def param(file):
    f = open(file, "r")
    f = f.read()
    sent = f.split(".")
    print('Total ' + str(len(sent)) + ' sentences') # Всего предложений
    words = f.split()
    print('Total '+ str(len(words)) + ' words') # Всего слов
    s = 0
    for w in words:
        s += len(w)
    print('Average length of a word is ' + str(s / len(words))) # Средняя длина слов
    s = 0
    for el in sent:
        s += len(list(el.split()))
    print('Average length of a sentence is ' + str(s / len(sent)) + ' words') # Среднее кол-во слов в предложении
    return 0

param('true.txt')
param('lie.txt')

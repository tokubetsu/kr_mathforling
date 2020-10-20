import requests
import bs4
import re
import json


def get_link(a, base_url='https://ru.wikipedia.org'):
    # с помощью регулярок вытаскивает ссылку на статью из всего содержимого тега, добавляя название ссылки
    string = str(a)
    pattern = r'.+?href="(.+?)"'
    href_part = re.search(pattern, string)
    href_part = href_part.group(1)
    link = base_url + href_part

    pattern = r'.+?title="(.+?)"'
    title = re.search(pattern, string)
    title = title.group(1)
    return link, title


def parsing_links(url):  # получает ссылки на все термины

    response = requests.get(url)
    bs_obj = bs4.BeautifulSoup(response.text, features='html.parser')

    page = []
    for p in bs_obj.find_all('p'):
        page.extend(p.find_all('a'))

    # <a href="/wiki/%D0%A1%D0%BE%D0%B1%D0%B0%D0%BA%D0%B0" title="Собака">собакой</a> - стандартная ссылка
    pattern = r'<a href=".+?" title=".+?">.+?</a>'
    page_new = [line for line in page if (re.match(pattern, str(line)) and str(line).find('span') == -1)]

    return page_new


def get_positions(url, lst):  # получает позиции элемента в списке
    position = []
    for key, item in enumerate(lst):
        if item == url:
            position.append(key)
    return position


def get_dict(url):  # составляет словарь терминов
    page = parsing_links(url)

    terms = {}
    list_links = []
    for line in page:
        link, title = get_link(line)
        # если ссылка не в списке ссылок, то добавляем ее туда
        if link not in list_links:
            list_links.append(link)
        # словарь: {term: {'link_find': list, 'link_inf': {link: list, }}, }, во втором словаре хранится,
        # когда встретилось это значение
        if title not in terms:
            terms[title] = {'link_find': [url, ], 'link_inf': {link: [url, ], }}
        else:
            if url not in terms[title]['link_find']:
                terms[title]['link_find'].append(url)
            if link not in terms[title]['link_inf']:
                terms[title]['link_inf'][link] = [url, ]
            else:
                if url not in terms[title]['link_inf'][link]:
                    terms[title]['link_inf'][link].append(url)

    return terms, list_links


def update_list(old_list, new_list):  # слияние двух списков
    for item in new_list:
        if item not in old_list:
            old_list.append(item)
    return old_list


def update_dict(old_dict, new_dict):  # слияние двух словарей
    for key in new_dict:
        # если такого ключа вообще не было, то просто добавить
        if key not in old_dict:
            old_dict[key] = new_dict[key]
        else:
            # слияние списков ссылок на изначальные страницы
            old_dict[key]['link_find'] = update_list(old_dict[key]['link_find'], new_dict[key]['link_find'])

            # слияние списков ссылок на страницы с терминами
            for item in new_dict[key]['link_inf']:
                if item not in old_dict[key]['link_inf']:
                    old_dict[key]['link_inf'][item] = new_dict[key]['link_inf'][item]
                else:
                    old_dict[key]['link_inf'][item] = update_list(old_dict[key]['link_inf'][item],
                                                                  new_dict[key]['link_inf'][item])

    return old_dict


def make_steps(n, base_url):
    terms = {}
    cur_urls = [base_url, ]

    for i in range(n + 1):
        cur_urls_new = []
        for url in cur_urls:
            terms_new, list_new = get_dict(url)
            cur_urls_new = update_list(cur_urls_new, list_new)
            terms = update_dict(terms, terms_new)
        cur_urls = cur_urls_new
        print(f'Step {i} of {n} completed')

    return terms


def main():
    url = input('Пожалуйста, введите ссылку: \n')
    n = int(input('Пожалуйста, введите глубину обхода: \n'))
    terms = make_steps(n, url)

    mode = input('Вывести результаты в консоль? Yes/No\n')
    if mode.lower() == 'yes':
        print('link_find - ссылка, где был обнаруден термин\nlink_inf - ссылка на информационную страницу\n')
        for term in terms:
            print(term)
            print('\t' + 'link_find:')
            for link in terms[term]['link_find']:
                print(f'\t\t{link}')
            print('\t' + 'link_inf:')
            for key in terms[term]['link_inf']:
                print(f'\t\t{key}\t \n\t\t\tбыла найдена в ссылках:')
                for item in terms[term]["link_inf"][key]:
                    print(f'\t\t\t\t{item}')

    mode = input('Сохранить в json-файл? Yes/No\n')
    if mode.lower() == 'yes':
        filename = input('Пожалуйста, введите имя файла в формате .json : \n')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(terms, f, ensure_ascii=False)


if __name__ == '__main__':
    main()

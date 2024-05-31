import os
import time
import pickle
import requests
from tqdm import tqdm


def generate_links(sm_numbers, letters, lg_numbers, projections, years, dsm=True):
    """

    :param sm_numbers: list
    :param letters: list
    :param lg_numbers: list
    :param projections: list
    :param years: list
    :param dsm: bool
    :return:
    """

    link_year = {
        '2018': '2018',
        '2019': '2019',
        '20170601': '2016'
    }

    links = []
    for sm_number in sm_numbers:
        sm_number = "%03d" % sm_number
        for letter in letters:
            for lg_number in lg_numbers:
                for projection in projections:
                    for year in years:
                        for i in range(1, 5):
                            for j in range(1, 5):
                                for k in range(1, 5):
                                    file = f'bc_0{lg_number}{letter}{sm_number}_{i}_{j}_{k}_{projection}_{year}'
                                    if dsm:
                                        file = f'{file}_dsm.laz'
                                    else:
                                        file = f'{file}.laz'
                                    link = f'https://nrs.objectstore.gov.bc.ca/gdwuts/0{lg_number}/0{lg_number}{letter}/{link_year[year]}/dsm/{file}'
                                    links.append(link)
    return links


no_name = generate_links([62, 71, 72, 81, 82, 92, 12, 21, 1, 2, 11, 31, 41], ['g', 'h', 'i', 'j'], ['82'],
                         ['xli_12_utm11'], ['2018'])
ndmp_fraser_2016 = generate_links(range(5, 96), ['g', 'h', 'i', 'j'], ['92'], ['xyes_8_utm10'], ['20170601'])
ndmp_kooteney_2018 = generate_links(range(1, 63), ['e', 'f', 'g'], ['82'], ['xli_12_utm11'], ['2018'])
ndmp_okanagan_2018 = generate_links(range(4, 64), ['e', 'l'], ['82'], ['cyes_12_utm11'], ['2018'], dsm=False)
ndmp_okanagan_19_1 = generate_links(range(1, 98), ['e', 'l'], ['82'], ['cyes_12_utm11'], ['2019'], dsm=False)
ndmp_okanagan_19_2 = generate_links(range(60, 100), ['h'], ['92'], ['cyes_12_utm11'], ['2019'], dsm=False)
LINKS = no_name + ndmp_fraser_2016 + ndmp_kooteney_2018 + ndmp_okanagan_2018 + ndmp_okanagan_19_1 + ndmp_okanagan_19_2


def extract_valid_links(links):
    valid_links = []
    for url in tqdm(links):
        try:
            response = requests.head(url)
        except:
            time.sleep(1)
            response = requests.head(url)
        if response.status_code != 404:
            valid_links.append(url)
            with open(f"../data/txt/{url.split('/')[-1]}.txt", 'wb') as file:
                pickle.dump(url, file)
    print(f"{len(valid_links)} valid links found")
    return


def download_files(directory):
    names = set([f"{file.split('.txt')[0]}" for file in os.listdir(directory)])
    missing_files = set.difference(names, set(os.listdir(f'../data/laz')))

    for file in tqdm(missing_files):
        url = pickle.load(open(f"{directory}/{file}.txt", 'rb'))
        with open(f'../data/laz/{file}', 'wb') as f:
            f.write(requests.get(url).content)
    print(f"{len(os.listdir('../data/laz'))} laz files in data/laz")


if __name__ == '__main__':
    download_files('../data/txt')


import requests
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm
from pydub import AudioSegment
import numpy as np
import psycopg2

def calculate_quality(audio_path):
    
    snr = calculate_snr(audio_path)
    return snr

def calculate_snr(audio_path):
    # Use pydub to load audio file
    audio = AudioSegment.from_file(audio_path)

    # Convert audio to NumPy array
    audio_array = np.array(audio.get_array_of_samples())

    # Calculate SNR (Signal-to-Noise Ratio)
    signal_power = np.sum(audio_array**2)
    
    # Assume some noise level for demonstration purposes
    noise_level = 1000

    snr = 10 * np.log10(signal_power / noise_level)
    return snr 

def get_chapters_links(input_url, root_link):

    internal_links = get_links(input_url)[0]
    # Keeps links whose address includes the name of the requested author
    links = [link for link in internal_links if root_link in link]
    return links


def get_mp3_links(mp3_url):

    try:
        website_content = requests.get(mp3_url.strip()).text
    except AssertionError as error:
        print(error)
        check_internet = requests.get('https://google.com').status_code

        if check_internet != requests.codes.ok:
            raise ConnectionError('ERROR: Check internet connection.')
    else:
        _soup = BeautifulSoup(website_content, features='html.parser')

        def with_string(src):  # function to define
            return src and re.compile('.*.mp3').search(src)

        links = []
        for link in _soup.find_all('source', src=with_string):
            links.append(link['src'])
        return links
    finally:
        pass


def download_mp3_files(url, links, file_path, parent_dir):

    author_root = url[:url.rfind('/')+1]
    print(f'\nauthor_root: {author_root}')
    full_links = [author_root + link for link in links]
    for link in tqdm(full_links, position=1, desc='link', leave=False,
                     colour='red', ncols=80):
        mp3_link = get_mp3_links(link)  # retrieves all the links where mp3 files are stored

        if len(mp3_link) == 0:  # no mp3 link found on this webpage
            root_link = link[link.rfind('/')+1:-5]  # local link of the book
            new_file_path = file_path + '\\' + root_link
            os.makedirs(new_file_path, exist_ok=True)
            new_links = get_chapters_links(link, root_link)  # new internal links
            new_full_links = [author_root + link for link in new_links]

            for new_link in new_full_links:
                new_mp3_link = get_mp3_links(new_link)

                if len(new_mp3_link) == 0:
                    print(f'new_mp3_link: {new_mp3_link}')
                    logfile = parent_dir+'\log.txt'
                    now = datetime.now() # current date and time
                    date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
                    with open(logfile, 'a+', encoding='utf-8') as f:
                        f.write('Logged time: ')
                        f.write(date_time)
                        f.write('\nWARNING: The new_link: "')
                        f.write(new_link)
                        f.write('"\n')
                        f.write('Very likely the website of this link has')
                        f.write(' several chapters or a link is wrong!\n\n')
                    continue

                mp3_link = new_mp3_link[0]
                doc = requests.get(mp3_link)
                filename = mp3_link[mp3_link.rfind('/')+1:]
                # Next line must be modified if using another root webpage
                new_filename = filename[filename.find('/albalearning-')+14:]
                with open(new_file_path+'\\'+new_filename, 'wb') as f:
                    f.write(doc.content)
                # Calculate quality
                quality_score = calculate_quality(new_file_path+'\\'+new_filename)
                # Insert into PostgreSQL database
                insert_into_database(url, root_link, new_file_path+'\\'+new_filename, quality_score)
        elif len(mp3_link) > 1:
            logfile = parent_dir+'\log.txt'
            now = datetime.now() # current date and time
            date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            with open(logfile, 'a+', encoding='utf-8') as f:
                f.write('Logged time: ')
                f.write(date_time)
                f.write('WARNING: More than one mp3 file have been found on: "')
                f.write(link)
                f.write('"\n')
                f.write('Very likely the website of this link has several')
                f.write(' versions.')
        else:
            mp3_link = mp3_link[0]
            doc = requests.get(mp3_link)
            filename = mp3_link[mp3_link.rfind('/')+1:]
            new_filename = filename[filename.rfind('-')+1:]  # renames file
            with open(file_path+'\\'+new_filename, 'wb') as f:
                f.write(doc.content)
    return None

def insert_into_database(url, author, file_path, quality_score):
    connection = None
    try:
        connection = psycopg2.connect(
            user="your_username",
            password="your_password",
            host="your_host",
            port="your_port",
            database="your_database"
        )

        cursor = connection.cursor()
        postgres_insert_query = """INSERT INTO AudioFiles (title, author, file_path, duration, quality_score) VALUES (%s, %s, %s, %s, %s)"""
        record_to_insert = ('Sample Audio', author, file_path, 120.5, quality_score)
        cursor.execute(postgres_insert_query, record_to_insert)

        connection.commit()
        print("Record inserted successfully into AudioFiles table")

    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into AudioFiles table", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


def filter_links(links):

    regex = re.compile(r'([#/]|(-en.)|(-fr.))')
    clean_links = [link for link in links if not regex.search(link)]
    return clean_links


def get_links(url):

    if not url or len(url) < 1:
        raise Exception('INFO: Invalid Input')
    try:
        website_content = requests.get(url.strip()).text
    except AssertionError as error:
        print(error)
        check_internet = requests.get('https://google.com').status_code

        if check_internet != requests.codes.ok:
            raise ConnectionError('ERROR: Check internet connection.')
    else:
        if len(website_content) == 0:
            raise Exception('INFO: Website was not retrieved!')
        _soup = BeautifulSoup(website_content, features='html.parser')

        internal_links = set()
        external_links = set()

        # We search for the links:
        for line in _soup.find_all('a'):
            link = line.get('href')
            if not link:
                continue
            if link.startswith('http'):
                external_links.add(link)
            else:
                internal_links.add(link)

        return [internal_links, external_links]
    finally:
        pass


def set_variables(web_root, author_keywords):

    abspath = os.path.abspath(__file__)
    parent_dir = os.path.dirname(abspath)
    os.chdir(parent_dir)
    user_input_urls = [web_root + elem + '/' for elem in author_keywords]

    return parent_dir, user_input_urls


def get_author_keywords(web_root):

    if not web_root or len(web_root) < 1:
        raise Exception('INFO: Invalid Input')
    try:
        website_content = requests.get(web_root.strip()).text
    except AssertionError as error:
        print(error)
        check_internet = requests.get('https://google.com').status_code

        if check_internet != requests.codes.ok:
            raise ConnectionError('ERROR: Check internet connection.')
    else:
        if len(website_content) == 0:
            raise Exception('INFO: Website was not retrieved!')
        _soup = BeautifulSoup(website_content, features='html.parser')

        author_list = []

        # We search for the author keywords list:
        for line in _soup.find_all('td', class_='lista-libros1'):
            for element in line.find_all('a'):
                author_key = element.get('href')
                if not author_key:
                    continue
                else:
                    author_list.append(author_key)

        return author_list
    finally:
        pass


def main():

    web_root = 'https://albalearning.com/audiolibros/'
    #author_keywords = ['benedetti', 'benavente', 'hesse']  # author list manually defined
    author_keywords = get_author_keywords(web_root)
    print(f'authors list: {author_keywords}')
    parent_dir, user_input_urls = set_variables(web_root, author_keywords)
    for url in tqdm(user_input_urls, position=0, desc='url', leave=True,
                    colour='green', ncols=80):
        links = get_links(url)[0]
        links = filter_links(links)
        folder = author_keywords[user_input_urls.index(url)]
        file_path = os.path.join(parent_dir, folder)
        os.makedirs(file_path, exist_ok=True)
        download_mp3_files(url, links, file_path, parent_dir)
    return None


if __name__ == '__main__':
    main()
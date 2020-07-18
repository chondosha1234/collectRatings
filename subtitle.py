import os
import json
import zipfile
import urllib.request
import requests
import wget
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

def check_folder(input):
    """
    Check folder with movie for .srt subtitle file
    Takes user input and compares names ??
    """
    movie_folder = spell_compare(input)
    path = "/Users/jmill/downloads/" + movie_folder
    for File in os.listdir(path):
        if File.endswith(".srt"):
            os.chdir(path)       #this changes working dir so I can find file
            file_stat = os.stat(File)
            size = file_stat.st_size / 1024  #shows size in kB
            if size < 50:
                return False
            return True
    return False

def find_id(movie_name):
    """
    Take movie_name input to search the yts / yify website for movie
    and return the imbd id if found, or return False if the query
    term is inaccurate
    """
    search = requests.get('https://yts.mx/api/v2/list_movies.json?query_term=' + movie_name)
    info = search.json()
    if info['data']['movie_count'] == 0:
        return False
    else:
        movie = search_compare(movie_name, info['data']['movies'])
        for element in info['data']['movies']:
            if element['title'] is movie:
                id = element['imdb_code']
        return id

def find_sub_url(id):
    """
    Takes the imbd id and searches the yify-subs website for a
    hyperlink reference that has english in its string.
    Returns a string that can be used to download.
    """
    site = requests.get('https://yts-subs.com/movie-imdb/' + id)
    html = site.text
    soup = BeautifulSoup(html, 'html.parser')
    html_list = soup.find_all('a')
    for link in html_list:
        if 'english' in link['href']:
            url = link['href'][11:] + '.zip'
            print(url)
            return url
    print('No Match')

def download_sub(sub_url, sub_name):
    """
    Download that subtitle file
    """
    print('Beginning download...')
    target_path = r"C:\\Users\\jmill\\Downloads\\" + sub_name + '.zip'
    wget.download('https://www.yifysubtitles.com/subtitle/' + sub_url, target_path)
    print()
    return target_path


def extract(sub_path, movie_folder):
    """
    Unzip or extract the files from download to the movie folder
    """
    #os.chdir(sub_path)   don't need i think
    with zipfile.ZipFile(sub_path, 'r') as zip_ref:
        zip_ref.extractall(movie_folder)
    print('Your subtitle is with your movie now!')

def spell_compare(input):
    """
    Compare user input to closest movie folder name
    """
    #create list of all download folders
    lst = os.listdir(r"C:\\Users\\jmill\\Downloads\\")
    input = input.casefold()
    #compare input to each item in list and return max ratio, which is closest
    best_guess = max(lst, key= lambda x: SequenceMatcher(None, input, x.casefold()).ratio())
    return best_guess

def search_compare(input, info):
    """
    Compares input to yify search results to find exact movie
    """
    movie_list = []
    for element in info:
        movie_list.append(element['title'])
    input = input.casefold()
    best_guess = max(movie_list, key= lambda x: SequenceMatcher(None, input, x.casefold()).ratio())
    return best_guess


def main():

    movie_name = input("Enter movie title: ")
    movie_folder = spell_compare(movie_name)
    if check_folder(movie_name):
        print("You already have subtitles!")
    else:
        id = find_id(movie_name)
        sub_url = find_sub_url(id)
        sub_path = download_sub(sub_url, movie_name)

        movie_path = r"C:\\Users\\jmill\\Downloads\\" + movie_folder
        extract(sub_path, movie_path)

if __name__ == "__main__":
    main()

import re
import requests
import gspread
from selenium import webdriver
from bs4 import BeautifulSoup
from test_dict import film_list  #change to movie_list

############################################################

##########   Score retrieving functions   ##################

###########################################################

def tomato_score_getter(url):
    dict = {}
    if url is None:
        dict['RT'], dict['AR'] = None, None
        return dict
    site = requests.get(url)
    html = site.text
    soup = BeautifulSoup(html, 'lxml')
    span = soup.find_all('span')    #scores are found in <span> tag
    scores, percentages = [], []

    for element in span:
        if element.get('class') == ['mop-ratings-wrap__percentage']:   #this class holds scores for movie
            percentages.append(element.string)  #gets the number from tag
    for element in percentages:
        s = re.sub('[^0123456789]', '', element)  #remove all empty space from string
        scores.append(s)

    if len(scores) == 2:
        dict['RT'], dict['AR'] = scores[0], scores[1]

    elif len(scores) == 1:
        a_list = soup.find_all('a')
        for element in a_list:
            if element.get('href') == '#audience_reviews':
                dict['RT'], dict['AR'] = None, scores[0]
            elif element.get('href') == '#contentReviews':
                dict['RT'], dict['AR'] = scores[0], None
    else:
        dict['RT'], dict['AR'] = None, None

    return dict


def imdb_score_getter(url):
    if url is None:
        return None, None
    site = requests.get(url)  #get imdb id from yify thing
    html = site.text
    soup = BeautifulSoup(html, 'lxml')
    span = soup.find_all('span')   #helps find imdb score
    div = soup.find_all('div')     #helps find metacritic score
    meta, ratings = [], []
    for element in span:
        if element.get('itemprop') == 'ratingValue':
            ratings.append(element)
    for element in ratings:
        score_str = element.string
        imdb_score = int(float(score_str) * 10)

    for element in div:
        if (element.get('class') == ['metacriticScore', 'score_unfavorable', 'titleReviewBarSubItem']) or (element.get('class') == ['metacriticScore', 'score_mixed', 'titleReviewBarSubItem']) or (element.get('class') == ['metacriticScore', 'score_favorable', 'titleReviewBarSubItem']):
            meta.append(element)
        score = str(meta)
        meta_score = re.sub('[^0123456789]', '', score)
        meta_score = meta_fixer(meta_score)

    return imdb_score, meta_score

def meta_fixer(s):
    lst, digits = [], []
    score = 0
    for element in s:
        lst.append(element)
    for digit in lst:
        digits.append(int(digit))
    if len(digits) == 1:
        score = digits[0]
    elif len(digits) == 2:
        score = digits[0]* 10 + digits[1]
    elif len(digits) == 3:
        score = 100
    else:
        score = None
    return score   # fixes metacritic score from imdb page

def LB_score_getter(url):
    if url is None:
        return None
    driver = webdriver.Chrome('C:/Users/jmill/Desktop/cs61a/project/ratings/chromedriver_win32/chromedriver.exe')
    driver.get(url)     #loads javascript
    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.close()
    a = soup.find_all('a')
    a_list = []
    for element in a:
        if (element.get('class') == ['tooltip', 'display-rating', '-highlight']) or (element.get('class') == ['tooltip', 'display-rating']):
            a_list.append(element.string)
    LB_score = int(float(a_list[0]) * 10) * 2
    return LB_score


###########################################################################

#############   updating    #########################

##########################################################################

def update():
    client = gspread.service_account(filename='C:/Users/jmill/Desktop/cs61a/project/ratings/client_secret.json')
    sheet = client.open('Test_sheet').sheet1
    titles = sheet.col_values(1)
    row_counter = 2
    updates = {}
    problems = {}
    movies = film_list  #change to real one

    for film in titles[1:]:
        new_scores = []
        try:
            imdb = imdb_score_getter(movies[film]['imdb'])
            new_scores.append(imdb[0])
            new_scores.append(imdb[1])
            if (new_scores[0] != sheet.cell(row_counter, 4).value) and (new_scores[0] is not None):
                updates[film] = [{'imdb': new_scores[0]}]
            if (new_scores[1] != sheet.cell(row_counter, 5).value) and (new_scores[1] is not None):
                if updates[film]:
                    updates[film].append({'mc': new_scores[1]})
                else:
                    updates[film] = [{'mc': new_scores[1]}]
        except:
            new_scores.append(None)
            new_scores.append(None)
            problems[film] = ['imdb', 'mc']

        try:
            new_scores.append(LB_score_getter(movies[film]['letterboxd']))
            if (new_scores[2] != sheet.cell(row_counter, 6).value) and (new_scores[2] is not None):
                if updates[film]:
                    updates[film].append({'LB': new_scores[2]})
                else:
                    updates[film] = [{'LB': new_scores[2]}]
        except:
            new_scores.append(None)
            if problems[film]:
                problems[film].append('LB')
            else:
                problems[film] = ['LB']
        try:
            tomatoes = tomato_score_getter(movies[film]['rottentomatoes'])
            new_scores.append(tomatoes['RT'])
            new_scores.append(tomatoes['AR'])
            if (new_scores[3] != sheet.cell(row_counter, 7).value) and (new_scores[3] is not None):
                if updates[film]:
                    updates[film].append({'RT': new_scores[3]})
                else:
                    updates[film] = [{'RT': new_scores[3]}]
            if (new_scores[4] != sheet.cell(row_counter, 8).value) and (new_scores[4] is not None):
                if updates[film]:
                    updates[film].append({'AR': new_scores[4]})
                else:
                    updates[film] = [{'AR': new_scores[4]}]
        except:
            new_scores.append(None)
            new_scores.append(None)
            if problems[film]:
                problems[film].extend(['RT', 'AR'])
            else:
                problems[film] = ['RT', 'AR']

        for i in range(1,6):
            if (new_scores[i-1] != None) and (new_scores[i-1] != sheet.cell(row_counter, i+3).value):
                sheet.update_cell(row_counter, (i+3), new_scores[i-1])
            else:
                pass
        row_counter += 1

    if updates:
        print()
        print('These movies have been updated: ')
        print()
        for movie in updates:
            print(movie + '   ' + str(updates[movie]))
    else:
        print()
        print('No films needed to be updated!')

    if problems:
        print()
        print('There were problems with these movies: ')
        for movie in problems:
            print(movie + '   ' + str(problems[movie]))
    else:
        print()
        print('There were no problems!')



def main():
    update()

if __name__ == '__main__':
    main()

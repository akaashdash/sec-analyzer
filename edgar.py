import os
from sec_edgar_downloader import Downloader
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup as bs
import re
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go


def download_filing(ticker, year):
    edgar_dir = os.path.join(os.getcwd(), 'sec-edgar-filings')
    ticker_dir = os.path.join(edgar_dir, ticker)
    filing_dir = os.path.join(ticker_dir, '10-K')
    year_dir = os.path.join(filing_dir, str(year))
    if os.path.exists(year_dir):
        return
    dl = Downloader()
    dl.get("10-K", ticker, amount=1, download_details=False, after=(str(year) + "-12-01"), before=(str(year + 1) + "-12-01"))
    if not os.path.exists(filing_dir):
        return
    for dl_dir in os.listdir(filing_dir):
        file_dir = os.path.join(filing_dir, dl_dir)
        if not os.path.isdir(file_dir):
            continue
        if not '-' in dl_dir:
            continue
        year = int(dl_dir.split('-')[1]) + 2000
        os.rename(file_dir, os.path.join(filing_dir, str(year)))


def download_all_filings(ticker):
    for i in range(2000, 2023):
        download_filing(ticker, i)


def clean_filing_submission(text):
    response = text
    response = re.sub(r'(\r\n|\r|\n)', ' ', response) # \r new line in macOS, \n in Unix and \r\n in Windows
    # remove certain text with regex query
    response = re.sub(r'<DOCUMENT>\s*<TYPE>(?:GRAPHIC|ZIP|EXCEL|PDF|XML|JSON).*?</DOCUMENT>', ' ', response)
    response = re.sub(r'<SEC-HEADER>.*?</SEC-HEADER>', ' ', response)
    response = re.sub(r'<IMS-HEADER>.*?</IMS-HEADER>', ' ', response)
    # replace characters to correct them
    response = re.sub(r'&nbsp;', ' ', response)
    response = re.sub(r'&#160;', ' ', response)
    response = re.sub(r'&amp;', '&', response)
    response = re.sub(r'&#38;', '&', response)
    # replace other encoded characters to whitespace
    response = re.sub(r'&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});', ' ', response)
    soup = bs(response, 'html.parser')
    for tag in soup.find_all('xbrl'):
        # don't remove if there is item detail
        fp_result = tag(text=re.compile(r'(?i)item\s*\d', re.IGNORECASE))
        event = len(fp_result)
        ## if no item details remove that part
        # decompose() method removes a tag as well as its inner content.
        if (event==0):
            tag.decompose()
    # remove tables
    for tag in soup.find_all('table'):
        temp_text = tag.get_text()
        numbers = sum(c.isdigit() for c in temp_text)
        letters = sum(c.isalpha() for c in temp_text)
        ratio_number_letter = 1.0
        if (numbers + letters) > 0:
            ratio_number_letter = numbers/(numbers + letters)

        event = 0
        if( (event==0) and ( ratio_number_letter > 0.1)):
            tag.decompose()
    ## remove other text between tags used for styling
    text = soup.get_text()
    text = re.sub(r'<(?:ix|link|xbrli|xbrldi).*?>.*?<\/.*?>', ' ', text)
    ## remove extra whitespace from sentences
    text = "".join(line.strip() for line in text.split("\n"))
    ## some additional cleaning
    text = re.sub(r'--;', ' ', text)
    text = re.sub(r'__', ' ', text)
    cleanr = re.compile(r'<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    text = re.sub(cleanr, ' ', text)
    temp_match = re.search(r'^.*?item(\s)*\d', text, flags=re.IGNORECASE)
    if temp_match != None: 
        text = re.sub(r'^.*?item(\s)*\d', '', text, count=1, flags=re.IGNORECASE)
    ## replace more than one whitespace with single whitespace
    text = re.sub(r'\s+', ' ', text)
    return text


def get_filing_data(text, year):
    df = pd.DataFrame([], columns=['Year', 'Words', 'Sentences'])
    tokenized_words = np.asarray(word_tokenize(text))
    word_count = len(tokenized_words)

    tokenized_sents = np.asarray(sent_tokenize(text))
    sent_count = len(tokenized_sents)

    df.loc[len(df.index)] = [year, word_count, sent_count] 
    return (df, tokenized_sents, tokenized_words)


def parse_filing(ticker, year):
    edgar_dir = os.path.join(os.getcwd(), 'sec-edgar-filings')
    ticker_dir = os.path.join(edgar_dir, ticker)
    filing_dir = os.path.join(ticker_dir, '10-K')
    year_dir = os.path.join(filing_dir, str(year))
    if not os.path.exists(year_dir):
        return
    parsed_file = os.path.join(year_dir, 'parsed.txt')
    metadata_file = os.path.join(year_dir, 'metadata.csv')
    words_file = os.path.join(year_dir, 'words')
    sents_file = os.path.join(year_dir, 'sentences')
    submission_file = os.path.join(year_dir, 'full-submission.txt')
    if os.path.exists(parsed_file) and \
        os.path.exists(metadata_file) and \
        os.path.exists(words_file) and \
        os.path.exists(sents_file):
        return
    
    with open(submission_file, encoding='utf-8') as f:
        text = f.read()
    
    cleaned_text = clean_filing_submission(text)

    with open(parsed_file, 'w') as f:
        f.write(cleaned_text)
    
    metadata, sentences, words = get_filing_data(cleaned_text, year)
    metadata.to_csv(metadata_file)
    sentences.tofile(sents_file)
    words.tofile(words_file)
    

def parse_all_filings(ticker):
    for i in range(2000, 2023):
        parse_filing(ticker, i)

def create_word_cloud(ticker, year):
    edgar_dir = os.path.join(os.getcwd(), 'sec-edgar-filings')
    ticker_dir = os.path.join(edgar_dir, ticker)
    filing_dir = os.path.join(ticker_dir, '10-K')
    year_dir = os.path.join(filing_dir, str(year))
    parsed_file = os.path.join(year_dir, 'parsed.txt')
    if not os.path.exists(parsed_file):
        return
    with open(parsed_file, encoding='utf-8') as f:
        text = f.read()
    stopwords = set(STOPWORDS)
    stopwords.update(["page", "table", 'document'])
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)
    plt.figure(figsize=(20, 50))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()

def create_plots(ticker):
    edgar_dir = os.path.join(os.getcwd(), 'sec-edgar-filings')
    ticker_dir = os.path.join(edgar_dir, ticker)
    filing_dir = os.path.join(ticker_dir, '10-K')
    if not os.path.exists(filing_dir):
        return
    dfs = []
    for subdir in os.listdir(filing_dir):
        year_dir = os.path.join(filing_dir, subdir)
        metadata_file = os.path.join(year_dir, 'metadata.csv')
        if not os.path.exists(metadata_file):
            continue
        dfs.append(pd.read_csv(metadata_file))
    df = pd.concat(dfs)

    df.sort_values('Year', inplace=True)
    fig_words = px.line(df, x=df['Year'], y=df['Words'])
    fig_words.show()

    fig_sents = px.line(df, x=df['Year'], y=df['Sentences'])
    fig_sents.show()


if __name__ == '__main__':
    ticker = 'JPM'
    download_all_filings(ticker)
    parse_all_filings(ticker)
    create_word_cloud(ticker, 2021)
    create_plots(ticker)
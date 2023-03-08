import os
from sec_edgar_downloader import Downloader
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup as bs
import re
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import json
import multiprocessing


class Filing:
    __dir = None
    year = None
    metadata = None

    def __init__(self, year_dir) -> None:
        self.__dir = year_dir
        self.year = int(os.path.basename(os.path.normpath(year_dir)))
        self.__load()

    def __load(self):
        parsed_file = os.path.join(self.__dir, 'parsed.txt')
        metadata_file = os.path.join(self.__dir, 'metadata.csv')
        words_file = os.path.join(self.__dir, 'words')
        sents_file = os.path.join(self.__dir, 'sentences')
        submission_file = os.path.join(self.__dir, 'full-submission.txt')
        if not (os.path.exists(parsed_file) and \
            os.path.exists(metadata_file)):
            self.__parse(parsed_file, metadata_file, words_file, sents_file, submission_file)
        else:
            self.metadata = pd.read_csv(metadata_file)

    def __parse(self, parsed_file, metadata_file, words_file, sents_file, submission_file):
        with open(submission_file, encoding='utf-8') as f:
            text = f.read()
        
        cleaned_text = self.__clean_filing_submission(text)

        with open(parsed_file, 'w') as f:
            f.write(cleaned_text)
        
        self.metadata, sentences, words = self.__get_filing_data(cleaned_text)
        self.metadata.to_csv(metadata_file, index=False)
        # sentences.tofile(sents_file)
        # words.tofile(words_file)
    
    def __clean_filing_submission(self, text):
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
        # replace other encoded characters to whitespac\
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
    
    def __get_filing_data(self, text):
        df = pd.DataFrame([], columns=['Year', 'Words', 'Sentences'])
        tokenized_words = np.asarray(word_tokenize(text))
        word_count = len(tokenized_words)

        tokenized_sents = np.asarray(sent_tokenize(text))
        sent_count = len(tokenized_sents)

        df.loc[len(df.index)] = [self.year, word_count, sent_count] 
        return (df, tokenized_sents, tokenized_words)
    
    def generate_word_cloud(self):
        parsed_file = os.path.join(self.__dir, 'parsed.txt')
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

class Company:
    __edgar_dir = 'sec-edgar-filings'
    __filing_type = '10-K'
    __filings = None
    cik = None
    ticker = None
    title = None

    def __init__(self, cik, ticker, title) -> None:
        self.cik = cik
        self.ticker = ticker
        self.title = title
        self.__download()
        self.__load()

    def __download(self):
        edgar_dir = os.path.join(os.getcwd(), self.__edgar_dir)
        cik_dir = os.path.join(edgar_dir, str(self.cik).zfill(10))
        filing_dir = os.path.join(cik_dir, self.__filing_type)
        if os.path.exists(filing_dir):
            return
        dl = Downloader()
        dl.get(self.__filing_type, str(self.cik), download_details=False)
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
        
    def __load(self):
        edgar_dir = os.path.join(os.getcwd(), self.__edgar_dir)
        cik_dir = os.path.join(edgar_dir, str(self.cik).zfill(10))
        filing_dir = os.path.join(cik_dir, self.__filing_type)
        if not os.path.exists(filing_dir):
            return
        dirs = []
        for year in os.listdir(filing_dir):
            year_dir = os.path.join(filing_dir, year)
            if os.path.isdir(year_dir):
                dirs.append(year_dir)
        # with multiprocessing.Pool(int(multiprocessing.cpu_count() / 2)) as pool:
        with multiprocessing.Pool() as pool:
            self.__filings = []
            for result in pool.map(Filing, dirs):
                self.__filings.append(result)

    def get_filings(self):
        return self.__filings
    
    def get_filing(self, year):
        query_result = list(filter(lambda filing: filing.year == year, self.__filings))
        if len(query_result) < 1:
            return None
        return query_result[0]
    
    def create_plots(self):
        dfs = []
        for filing in self.__filings:
            dfs.append(filing.metadata)
        df = pd.concat(dfs)
        df.sort_values('Year', inplace=True)
        
        fig_words = px.line(df, x=df['Year'], y=df['Words'])
        fig_words.show()

        fig_sents = px.line(df, x=df['Year'], y=df['Sentences'])
        fig_sents.show()


class CompanyFactory:
    __url = 'https://www.sec.gov/files/company_tickers.json'
    __file_name = 'company_tickers.json'
    __data = None

    def __init__(self) -> None:
        company_tickers_file = os.path.join(os.getcwd(), self.__file_name)
        if not os.path.exists(company_tickers_file):
            self.__download(company_tickers_file)
        self.__load(company_tickers_file)
    
    def __download(self, file):
        response = requests.get(self.__url)
        with open(file, 'wb') as f:
            f.write(response.content)

    def __load(self, file):
        self.__data = pd.read_json(file, orient='index')

    def from_ticker(self, ticker):
        mask = self.__data['ticker'].values == ticker
        result = self.__data[mask]
        if len(result) < 1:
            return None
        return Company(result.values[0][0], result.values[0][1], result.values[0][2])
    
    def from_title(self, title):
        mask = self.__data['title'].values == title
        result = self.__data[mask]
        if len(result) < 1:
            return None
        return Company(result.values[0][0], result.values[0][1], result.values[0][2])
    
    def from_cik(self, cik):
        mask = self.__data['cik_str'].values == int(cik)
        result = self.__data[mask]
        if len(result) < 1:
            return None
        return Company(result.values[0][0], result.values[0][1], result.values[0][2])

if __name__ == '__main__':
    cf = CompanyFactory()
    company = cf.from_ticker('NVDA')
    if not company == None:
        company.create_plots()
        filing = company.get_filing(2023)
        if not filing == None:
            filing.generate_word_cloud()
import os
from sec_edgar_downloader import Downloader
import requests
import json
import multiprocessing
import pandas as pd
from edgar_parser import process_filing
from wordcloud import WordCloud, STOPWORDS
import plotly.express as px

# TO FIND DATES FOR A YEAR USE https://data.sec.gov/submissions/CIK0000019617.json
# REPLACE CIK WITH THE RIGHT CIK AND LOOK FOR fiscalYearEnd (60-90 years)

class Filing:
    __dir = None
    year = None
    __len = 0

    def __init__(self, year_dir) -> None:
        self.__dir = year_dir
        self.year = int(os.path.basename(os.path.normpath(year_dir)))
        self.__load()

    def __load(self):
        parsed_file = os.path.join(self.__dir, 'parsed.json')
        submission_file = os.path.join(self.__dir, 'full-submission.txt')
        if not os.path.exists(parsed_file):
            self.__parse(parsed_file, submission_file)
        else:
            with open(parsed_file, encoding='utf-8') as f:
                content = json.load(f)
            for attribute, value in content.items():
                self.__len += len(value.split())

    def __parse(self, parsed_file, submission_file):
        with open(submission_file, encoding='utf-8') as f:
            text = f.read()
        content = process_filing(text)
        if content is not None:
            for attribute, value in content.items():
                self.__len += len(value.split())
            with open(parsed_file, 'w') as f:
                json.dump(content, f, indent=4)

    def generate_word_cloud(self):
        image_file = os.path.join(self.__dir, 'wordcloud.jpg')
        if os.path.exists(image_file):
            return image_file
        parsed_file = os.path.join(self.__dir, 'parsed.json')
        if not os.path.exists(parsed_file):
            return
        with open(parsed_file) as f:
            data = json.load(f)
        wordcloud = WordCloud(background_color="white").generate(data["item_1"])
        image = wordcloud.to_image()
        image.save(image_file)
        return image_file
    
    def get_length(self):
        return self.__len


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
        with multiprocessing.Pool() as pool:
            self.__filings = []
            for result in pool.map(Filing, dirs):
                self.__filings.append(result)
        self.plot_words()

    def get_filings(self):
        return self.__filings
    
    def get_filing(self, year):
        query_result = list(filter(lambda filing: filing.year == year, self.__filings))
        if len(query_result) < 1:
            return None
        return query_result[0]
    
    def plot_words(self):
        edgar_dir = os.path.join(os.getcwd(), self.__edgar_dir)
        cik_dir = os.path.join(edgar_dir, str(self.cik).zfill(10))
        filing_dir = os.path.join(cik_dir, self.__filing_type)
        if not os.path.exists(filing_dir):
            return
        plot_file = os.path.join(filing_dir, 'wordplot.jpg')
        if os.path.exists(plot_file):
            return plot_file
        data = { "years": [], "words": [] }
        for filing in self.get_filings():
            data['years'].append(filing.year)
            data['words'].append(filing.get_length())
        df = pd.DataFrame.from_dict(data)
        df.sort_values('years', inplace=True)
        fig_words = px.line(df, x=df['years'], y=df['words'])
        fig_words.write_image(plot_file)
        return plot_file


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
    company = cf.from_ticker('GOOG')
    print(company.plot_words())
    print(company.get_filing(2022).generate_word_cloud())
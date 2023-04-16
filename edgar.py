import os
from sec_edgar_downloader import Downloader
import requests
import json
import multiprocessing
import pandas as pd
from edgar_parser import process_filing
from visualizer import extract_entity_rel, generate_wordcloud, generate_knowledgegraph

# TO FIND DATES FOR A YEAR USE https://data.sec.gov/submissions/CIK0000019617.json
# REPLACE CIK WITH THE RIGHT CIK AND LOOK FOR fiscalYearEnd (60-90 years)

class Filing:
    __dir = None
    __submission_file_name = 'full-submission.txt'
    __parsed_file_name = 'cleaned.json'
    __wordcloud_file_name = 'wordcloud.jpg'
    __entity_rel_file_name = 'entity_rel.json'
    __knowledgegraph_file_name = 'kg.jpg'
    year = None

    def __init__(self, year_dir) -> None:
        self.__dir = year_dir
        self.year = int(os.path.basename(os.path.normpath(year_dir)))
        self.__load()

    def __load(self):
        if not os.path.exists(os.path.join(self.__dir, self.__parsed_file_name)):
            self.__parse()

    def __parse(self):
        with open(os.path.join(self.__dir, self.__submission_file_name), encoding='utf-8') as f:
            text = f.read()
        content = process_filing(text)
        if content is not None:
            with open(os.path.join(self.__dir, self.__parsed_file_name), 'w') as f:
                json.dump(content, f, indent=4)

    def __generate_entity_rel(self):
        entity_rel_file = os.path.join(self.__dir, self.__entity_rel_file_name)
        if not os.path.exists(entity_rel_file):
            parsed_file = os.path.join(self.__dir, self.__parsed_file_name)
            with open(parsed_file, encoding='utf-8') as f:
                data = json.load(f)
            extract_entity_rel(data, entity_rel_file)
        with open(entity_rel_file, encoding='utf-8') as f:
            data = json.load(f)
            return data    

    def get_wordcloud(self):
        wordcloud_file = os.path.join(self.__dir, self.__wordcloud_file_name)
        if os.path.exists(wordcloud_file):
            return wordcloud_file
        data = self.__generate_entity_rel()
        generate_wordcloud(data, wordcloud_file)
        return wordcloud_file
    
    def get_knowledgegraph(self):
        knowledgegraph_file = os.path.join(self.__dir, self.__knowledgegraph_file_name)
        if os.path.exists(knowledgegraph_file):
            return knowledgegraph_file
        data = self.__generate_entity_rel()
        generate_knowledgegraph(data, knowledgegraph_file)
        return knowledgegraph_file


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
        # USE DATES TO GET ONLY SPECIFIC YEAR
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

    def get_filings(self):
        return self.__filings
    
    def get_filing(self, year):
        query_result = list(filter(lambda filing: filing.year == year, self.__filings))
        if len(query_result) < 1:
            return None
        return query_result[0]


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
    company = cf.from_ticker('MSFT')
    print(company.get_filing(2022).get_wordcloud())
    print(company.get_filing(2022).get_knowledgegraph())
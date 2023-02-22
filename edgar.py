import os
from sec_edgar_downloader import Downloader
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup as bs
import re
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize
from transformers import pipeline


ticker = 'NCR'


dl = Downloader()
dl.get("10-K", ticker, amount=25)

most_recent = None

edgar_dir = os.path.join(os.getcwd(), 'sec-edgar-filings')
for ticker_dir in os.listdir(edgar_dir):
    filing_dir = os.path.join(edgar_dir, ticker)
    filing_dir = os.path.join(filing_dir, '10-K')
    for year_dir in os.listdir(filing_dir):
        year = year_dir.split('-')[1]

        with open(os.path.join(file_dir, 'full-submission.txt'), encoding='utf-8') as f:
            text = f.read()
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

        if int(year) == 22:
            most_recent = text

        print(year)
        print("----------------------------")
        tokenized_words = word_tokenize(text)
        print("Number of words: ", len(tokenized_words))
        print("Sample of words: ", tokenized_words[:10])

        tokenized_sents = sent_tokenize(text)
        print("Number of sentences: ", len(tokenized_sents))
        print("Sample of sentences: ", tokenized_sents[100:104])

if most_recent != None:
    stopwords = set(STOPWORDS)
    stopwords.update(["page", "table", 'document'])
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(most_recent)

    # Display the generated image:
    plt.figure(figsize=(20, 50))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()

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
import plotly.express as px
import plotly.graph_objects as go


ticker = 'CMG'


dl = Downloader()
dl.get("10-K", ticker, amount=25)

most_recent = None
df = pd.DataFrame([], columns=['Year', 'Words', 'Sentences'])

edgar_dir = os.path.join(os.getcwd(), 'sec-edgar-filings')
for ticker_dir in os.listdir(edgar_dir):
    filing_dir = os.path.join(edgar_dir, ticker)
    if not os.path.isdir(filing_dir):
        continue
    filing_dir = os.path.join(filing_dir, '10-K')
    for year_dir in os.listdir(filing_dir):
        file_dir = os.path.join(filing_dir, year_dir)
        if not os.path.isdir(file_dir):
            continue

        year = int(year_dir.split('-')[1])
        if year < 24:
            year += 2000
        else:
            year += 1900

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

        if int(year) == 2022:
            most_recent = text

        tokenized_words = word_tokenize(text)
        word_count = len(tokenized_words)

        tokenized_sents = sent_tokenize(text)
        sent_count = len(tokenized_sents)

        df.loc[len(df.index)] = [year, word_count, sent_count] 

df.sort_values('Year', inplace=True)
fig_words = px.line(df, x=df['Year'], y=df['Words'])
fig_words.show()

fig_sents = px.line(df, x=df['Year'], y=df['Sentences'])
fig_sents.show()

if most_recent != None:
    stopwords = set(STOPWORDS)
    stopwords.update(["page", "table", 'document'])
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(most_recent)

    # Display the generated image:
    plt.figure(figsize=(20, 50))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()

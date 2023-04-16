import json
from wordcloud import WordCloud, STOPWORDS
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from flair.nn import Classifier
from flair.splitter import SegtokSentenceSplitter
from flair.data import Sentence
tagger = Classifier.load('ner-fast')
extractor = Classifier.load('relations')
splitter = SegtokSentenceSplitter()

def extract_entity_rel(data, file):
    #sentences = splitter.split(data["item_1"])
    sentences = Sentence(data["item_1"])
    tagger.predict(sentences)
    extractor.predict(sentences)
    ent_dict = {}
    rel_dict = {}
    for entity in sentences.get_labels('ner'):
        name = entity.data_point.text
        label = entity.value
        score = entity.score
        if score < 0.7:
            continue
        if name not in ent_dict or score > ent_dict[name]['score']:
            ent_dict[name] = {'label': label, 'score': score}
    relations = sentences.get_labels('relation')
    for relation in relations:
        name = relation.data_point.text
        label = relation.value
        score = relation.score
        if score < 0.7:
            continue
        if name not in rel_dict or score > rel_dict[name]['score']:
            rel_dict[name] = {'label': label, 'score': score}
    extraction = {'entities': ent_dict, 'relationships': rel_dict}
    with open(file, 'w') as f:
        json.dump(extraction, f, indent=4)

def generate_wordcloud(data, file):
    wordcloud = WordCloud(background_color="white").generate(' '.join(data["entities"].keys()))
    image = wordcloud.to_image()
    image.save(file)

def generate_knowledgegraph(data, file):
    G = nx.DiGraph()
    nodes = []
    for key in data['entities'].keys():
        nodes.append((key, data['entities'][key]))
    #G.add_nodes_from(nodes)
    for key in data['relationships'].keys():
        ents = key.split(' -> ')
        G.add_edge(ents[0], ents[1], label=data['relationships'][key]['label'], score=data['relationships'][key]['score'])

    plt.figure(figsize=(15, 15))
    df = pd.DataFrame(index=G.nodes(), columns=G.nodes())
    for row, data in nx.shortest_path_length(G):
        for col, dist in data.items():
            df.loc[row,col] = dist

    df = df.fillna(df.max().max())
    layout = nx.kamada_kawai_layout(G, dist=df.to_dict())
    nx.draw(G, layout, edge_color='black', width=1, linewidths=1,
    node_size=600, node_color='pink',
    labels={node: node for node in G.nodes()})
    edge_labels = dict([((n1, n2), d['label'])
                    for n1, n2, d in G.edges(data=True)])
    nx.draw_networkx_edge_labels(G, layout, edge_labels=edge_labels, label_pos=0.5,
                             font_color='red', font_size=10)
    plt.savefig(file, format=file.split('.')[1])
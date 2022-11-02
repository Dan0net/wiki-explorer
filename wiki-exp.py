import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# relations = {
#     'parent': ['is'],
#     'related': ['related', 'on'],
#     'child': ['used']
# }

base_uri = 'https://en.wikipedia.org'
nodes = []
edges = []

def load_article(page_uri, depth=0, max_links=10, parent_uri=None, child_uri=None):
    html_text = requests.get(urljoin(base_uri, page_uri)).text
    soup = BeautifulSoup(html_text, 'html.parser')

    title = soup.find('span', {'class': 'mw-page-title-main'}).text

    img_url = 'https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/330px-Wikipedia-logo-v2.svg.png'
    hatnote = soup.find('div', {'class': 'hatnote'})
    # hatnote = soup.find('div', {'id': 'mw-content-text'})
    if hatnote:
        links = hatnote.find_all('a')
        if len(links) > 1:
            article_url = links[1].get('href')
            article_text = requests.get(urljoin(base_uri, article_url)).text
            article_soup = BeautifulSoup(article_text, 'html.parser')
            article_context = article_soup.find('div', {'id': 'mw-content-text'})
            [x.extract() for x in article_context.find_all('table', {'class': 'metadata'})]
            img = article_context.find('img')
            if article_context:
                img = article_context.find('img')
            if img:
                img_url = img.get('src')

    subcats = soup.find('div', {'id': 'mw-subcategories'})
    supcats = soup.find('div', {'class': 'mw-normal-catlinks'})

    size = 50
    if subcats:
        subcats_text = subcats.find('p').text
        if subcats_text:
            subcats_count = re.search(r'\d+', subcats_text)
            if subcats_count:
                size = 50+int(subcats_count.group())*5

    nodes.append({'data': {'id': page_uri, 'label': title, 'img_url': img_url, 'size': size}})

    if parent_uri:
        edges.append({'data': {'source': parent_uri, 'target': page_uri}, 'classes': 'parent'})

    if child_uri:
        print(title)
        edges.append({'data': {'source': page_uri, 'target': child_uri}})

    if depth > 0:
        link_count = 0
        
        # body = soup.find('div', {'id': 'mw-content-text'})
        # first_p = body.find('p')
        if subcats:
            # links = first_p.find_all('a')
            links = subcats.find_all('a')

            for link in links:
                # print(link)
                if not link.get('href').startswith('#'):
                    # print(link)
                    # print(link.previousSibling)
                    load_article(link.get('href'), depth=depth-1, child_uri=page_uri)
        if supcats:
            # links = first_p.find_all('a')
            links = supcats.find_all('a')[1:]

            for link in links:
                if not link.get('href').startswith('#'):
                    # print(link)
                    # print(link.previousSibling)
                    load_article(link.get('href'), depth=depth-1, parent_uri=page_uri)

load_article('/wiki/Category:Oils', depth=1, max_links=5)


from dash import Dash, html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
cyto.load_extra_layouts()
app = Dash(__name__)

app.layout = html.Div([
    html.P("Dash Cytoscape:"),
    cyto.Cytoscape(
        id='cytoscape',
        elements=nodes+edges,
        layout={'name': 'cose', 'directed': True},
        style={'width': '1600px', 'height': '1200px'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    'background-fit': 'cover',
                    'background-image': 'data(img_url)'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'arrow-scale': 2
                }
            },
            {
                'selector': '.parent',
                'style': {
                    'line-color': 'red',
                    'target-arrow-color': 'red',
                }
            }
        ]
    ),
    html.P(id='cytoscape-mouseoverNodeData-output')
])

@app.callback(
    Output('cytoscape','elements'),
    Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    if data:
        print(data['id'])
        load_article(data['id'], depth=1, max_links=5)
        # print(nodes)
    return nodes+edges

app.run_server(debug=True)
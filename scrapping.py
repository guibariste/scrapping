
import requests
from bs4 import BeautifulSoup

import pandas as pd
from urllib.parse import urljoin

# Fonction pour normaliser les titres pour la construction des URLs


# Fonction pour extraire les titres et construire les URLs de détails
def extract_and_check_detail_urls(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = soup.select('.desc-block .desc h3 a')
    detail_urls = []
    for title in titles:
        detail_url = urljoin(url, title.get('href'))
        detail_urls.append(detail_url)
    return detail_urls

# Fonction pour vérifier l'accès aux pages de détails et extraire les données
def get_page_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f'Accessible: {url}')
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        else:
            print(f'Non accessible (status code {response.status_code}): {url}')
            
       
            return None
    except requests.RequestException as e:
        print(f'Erreur d\'accès à {url}: {e}')
        return None

# Fonction pour extraire les données spécifiques de la div avec la classe title-block
def extract_title_block_data(soup):
    data = {}
    
    title_block = soup.select_one('.title-block')
    if title_block:
        date = title_block.select_one('.event-date')
        title = title_block.select_one('h1 span')
        description = title_block.select_one('p')
        
        data['Date'] = date.get_text(strip=True) if date else None
        data['Titre'] = title.get_text(strip=True) if title else None
        data['Description'] = description.get_text(strip=True) if description else None
    else:
        data['Date'] = None
        data['Titre'] = None
        data['Description'] = None
    
    return data

# Fonction pour extraire les données en fonction des sélecteurs CSS
def extract_data(soup, column_mapping):
    data = {}
    
    for column_name, selector in column_mapping.items():
        if selector == '.btn.btn-blue':
            button = soup.select_one(selector)
            data[column_name] = "oui" if button else "non"
        
        elif selector == '.with-doc-mark':
            doc = soup.select_one(selector)
            data[column_name] = "oui" if doc else "non"
        
        elif selector == 'img.image.image-style-event-page':
            img = soup.select_one(selector)
            if img and 'src' in img.attrs:
                img_src = img['src']
                base_url = 'https://www.bpifrance.fr'
                img_url = urljoin(base_url, img_src)
                data['lien-image'] = img_url
            else:
                data['lien-image'] = None
        
        else:
            element = soup.select_one(selector)
            data[column_name] = element.get_text(strip=True) if element else None
    
    return data

# Fonction pour collecter les données des pages de détails
def check_and_extract_data(detail_urls):
    data_list = []
    for detail_url in detail_urls:
        soup = get_page_content(detail_url)
        if soup:
            title_block_data = extract_title_block_data(soup)
            other_data = extract_data(soup, column_mapping)
            data = {**title_block_data, **other_data}
            data_list.append(data)
    return data_list

# URL de la première page
base_url = 'https://www.bpifrance.fr/nos-appels-a-projets-concours?page='

# Nombre total de pages à scraper
num_pages = 5

# Mapping des noms de colonnes aux sélecteurs CSS
column_mapping = {
    'Rubrique': '.rubrique',
    'Label': '.card-label',
    'lien-image': 'img.image.image-style-event-page',
    'Lien direct pour postuler(OUI/NON)': '.btn.btn-blue',
    "liens telechargeables(OUI/NON)": '.with-doc-mark',
    "divers": '.body-content'
}

# Scraper chaque page et vérifier les pages de détails
all_data = []
for page_number in range(num_pages):
    url = base_url + str(page_number)
    detail_urls = extract_and_check_detail_urls(url)
    page_data = check_and_extract_data(detail_urls)
    all_data.extend(page_data)

# Créer un DataFrame avec les noms de colonnes spécifiés
df = pd.DataFrame(all_data)

# Supprimer les lignes où toutes les colonnes sont vides
df_cleaned = df.dropna(how='any')

# Exporter le DataFrame nettoyé en fichier CSV
csv_filename = 'data.csv'
df_cleaned.to_csv(csv_filename, index=False)

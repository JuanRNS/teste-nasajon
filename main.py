import pandas as pd
import requests
import unicodedata
import os
from dotenv import load_dotenv
from rapidfuzz import process, utils

load_dotenv()

email = os.getenv("USER_EMAIL")
password = os.getenv("USER_PASSWORD")
api_key = os.getenv("API_KEY")
# Função para obter token de acesso
def get_acess_token():
    url_acess_token = "https://mynxlubykylncinttggu.supabase.co/auth/v1/token?grant_type=password"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "password": password
    }   
    try:
        response = requests.post(url_acess_token, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['access_token']
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter token de acesso: {e}")
        return None
    

# Remover acentos e caracteres especiais
def normalize_name(text):
    if not isinstance(text, str):
        return ""
   
    text_nfkd = unicodedata.normalize('NFKD', text)
    text_limpo = "".join([c for c in text_nfkd if not unicodedata.combining(c)])
    return utils.default_process(text_limpo)

# Carregar dados do IBGE
def get_ibge_data():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        ibge_dict = {}
        for m in data:
            name_norm = normalize_name(m['nome'])
            if name_norm not in ibge_dict:
                ibge_dict[name_norm] = []
            ibge_dict[name_norm].append(m)
        return ibge_dict
    except Exception:
        return None

# Lógica de Matching
def find_best_match(name, ibge_dict):
    if ibge_dict is None:
        return 'ERRO_API', None
        
    normalized_name = normalize_name(name)
    
    if normalized_name in ibge_dict:
        matches = ibge_dict[normalized_name]
        if len(matches) > 1:
            return 'AMBIGUO', None
        return 'OK', matches[0]
    
    choices = ibge_dict.keys()
    result = process.extractOne(normalized_name, choices)
    if result:
        best_match, score, _ = result
        if score > 80:
            matches = ibge_dict[best_match]
            if len(matches) > 1:
                return 'AMBIGUO', None
            return 'OK', matches[0]
            
    return 'NAO_ENCONTRADO', None

# Processamento
def data_processing(acess_token):
    ibge_data = get_ibge_data()
    
    try:
        df = pd.read_csv('input.csv')
    except Exception as e:
        print(f"Erro ao ler input.csv: {e}")
        return

    resultados = []
    
    for _, row in df.iterrows():
        municipio_input = str(row['municipio'])
        populacao_input = row['populacao']
        
        status, match_data = find_best_match(municipio_input, ibge_data)
        
        if status == 'OK' and match_data:
            municipio_ibge = match_data['nome']
            uf_dict = match_data.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {})
            uf = uf_dict.get('sigla', '')
            regiao = uf_dict.get('regiao', {}).get('nome', '')
            id_ibge = match_data.get('id', '')
        else:
            municipio_ibge = ''
            uf = ''
            regiao = ''
            id_ibge = ''
            
        resultados.append({
            'municipio_input': municipio_input,
            'populacao_input': populacao_input,
            'municipio_ibge': municipio_ibge,
            'uf': uf,
            'regiao': regiao,
            'id_ibge': id_ibge,
            'status': status
        })
    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_csv('resultado.csv', index=False)
    print("Arquivo resultado.csv gerado com sucesso!")
    
    stats = {}

    # Estatísticas
    total_municipios = len(df_resultado)
    total_ok = (df_resultado['status'] == 'OK').sum()
    total_nao_encontrado = (df_resultado['status'] == 'NAO_ENCONTRADO').sum()
    total_erro_api = (df_resultado['status'] == 'ERRO_API').sum()
    df_ok = df_resultado[df_resultado['status'] == 'OK']
    pop_total_ok = df_ok['populacao_input'].sum()
    # Calculo das estatísticas
    stats = {
        "total_municipios": int(total_municipios),
        "total_ok": int(total_ok),
        "total_nao_encontrado": int(total_nao_encontrado),
        "total_erro_api": int(total_erro_api),
        "pop_total_ok": float(pop_total_ok) if pd.notnull(pop_total_ok) else 0.0,
        "medias_por_regiao": {}
    }
    
    if not df_ok.empty:
        medias_por_regiao = df_ok.groupby('regiao')['populacao_input'].mean()
        for regiao, media in medias_por_regiao.items():
            if pd.notnull(media):
                stats['medias_por_regiao'][regiao] = round(float(media), 2)
    else:
        print("  Nenhum município OK para calcular médias.")
    
    # Enviar dados para o Supabase
    url_post_ibge = "https://mynxlubykylncinttggu.functions.supabase.co/ibge-submit"
    payload = {
        "stats" : stats
    }
    headers = {
        "Authorization": f"Bearer {acess_token}",
        "Content-Type": "application/json"
    }
    try: 
        response = requests.post(url_post_ibge, json=payload,headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Score: {data['score']}")
            print(f"Feedback: {data['feedback']}")
        else:
            print(f"Erro ao enviar dados para o Supabase: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao enviar dados para o Supabase: {e}")
if __name__ == '__main__':
    acess_token = get_acess_token()
    if acess_token:
        data_processing(acess_token)
    else:
        print("Erro ao obter token de acesso.")

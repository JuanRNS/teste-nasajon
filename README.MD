Crie um ambiente virtual
python -m venv .venv

### No Windows:
.venv\Scripts\activate

### No Linux/Mac:
source .venv/bin/activate

Instale as dependências:
pip install -r requirements.txt

Prepare o arquivo de entrada:
Certifique-se de que o arquivo input.csv está na raiz do projeto conforme o modelo fornecido.

Configure as Variáveis de Ambiente:
Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:

USER_EMAIL=seu_email@exemplo.com
USER_PASSWORD=sua_senha
API_KEY=sua_api_key_do_supabase

Execute o script:
python main.py


Tecnologias e Técnicas Utilizadas
Pandas: Para manipulação eficiente do CSV e cálculos estatísticos.

Requests: Para consumo das APIs (IBGE e Supabase).

Fuzzy Matching (RapidFuzz): Implementado para resolver erros de digitação e acentuação nos nomes dos municípios.

Normalização Unicode: Tratamento de caracteres especiais para garantir a precisão no cruzamento de dados.

Automação de Auth: Fluxo completo de obtenção de token JWT para autenticação Bearer.

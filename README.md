# 🥗 Sistema de Auxiliar em Nutrição - Versão 2.0

Um aplicativo web interativo para auxiliar nos estudos de nutrição, com calculadoras avançadas e acompanhamento alimentar.

## ✨ Principais Funcionalidades

### 1. **Calculadoras de Nutrição**
- **IMC** - Calcula o Índice de Massa Corporal com interpretação automática
- **TMB & TDEE** - Calcula Taxa Metabólica Basal e Gasto Energético Total Diário usando a fórmula Mifflin-St Jeor
- **Macronutrientes** - Distribui calorias em proteína, carboidratos e gordura com visualização em gráfico
- **Banco de Alimentos** - Consulta e adiciona alimentos com seus valores calóricos
- **Assistente IA** - Tire dúvidas de nutrição, matérias e rotina de estudos com suporte de modelo de linguagem

### 2. **Diário Alimentar**
- Registre suas refeições diárias
- Acompanhe calorias por refeição
- Compare com suas metas de nutrição

### 3. **Análise de Dados**
- Visualize histórico de cálculos
- Gráficos dos alimentos mais calóricos
- Relatórios nutricionais

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Executar a aplicação:**
```bash
python -m streamlit run app.py
```

3. **Configurar a chave OpenAI (opcional)**
- Gere uma chave em `https://platform.openai.com/account/api-keys`
- Defina a variável de ambiente `OPENAI_API_KEY`, ou crie `.streamlit/secrets.toml` com:
  ```toml
  OPENAI_API_KEY = "sua-chave-aqui"
  ```
- Não compartilhe essa chave e não a coloque no repositório público.

4. **Acessar no navegador:**
```
http://localhost:8501
```

## 📦 Dependências

- **streamlit** (>=1.56.0) - Framework web interativo
- **pandas** (>=3.0.0) - Análise e manipulação de dados
- **plotly** (>=6.7.0) - Gráficos interativos
- **openai** (>=1.0.0) - Integração com assistente de IA para dúvidas de estudo

## 🎓 Conceitos Nutricionais

### IMC (Índice de Massa Corporal)
- **Fórmula**: IMC = Peso (kg) / Altura (m)²
- **Categorias**:
  - Abaixo do peso: < 18.5
  - Peso normal: 18.5 - 24.9
  - Sobrepeso: 25 - 29.9
  - Obesidade: ≥ 30

### TMB (Taxa Metabólica Basal)
- Calorias queimadas em repouso absoluto
- **Fórmula de Mifflin-St Jeor**:
  - Homem: 10 × peso(kg) + 6.25 × altura(cm) - 5 × idade + 5
  - Mulher: 10 × peso(kg) + 6.25 × altura(cm) - 5 × idade - 161

### TDEE (Total Daily Energy Expenditure)
- Gasto calórico total diário
- **Fórmula**: TDEE = TMB × Fator de Atividade
- **Fatores de atividade**:
  - Sedentário: 1.2
  - Levemente ativo: 1.375
  - Moderadamente ativo: 1.55
  - Muito ativo: 1.725
  - Atleta: 1.9

### Macronutrientes
- **Proteína**: 4 calorias/grama (importante para musculatura)
- **Carboidratos**: 4 calorias/grama (energia)
- **Gordura**: 9 calorias/grama (hormônios e absorção de vitaminas)

## 💡 Dicas de Uso

### Para Perder Peso
- Calcule seu TDEE
- Consuma 80% do TDEE (déficit de 20%)
- Mantenha ingesta de proteína adequada (1.6-2.2g por kg)

### Para Ganhar Massa Muscular
- Calcule seu TDEE
- Consuma 110% do TDEE (superávit de 10%)
- Aumente proteína (1.8-2.2g por kg)

### Proporções Recomendadas
- **Proteína**: 25-35% das calorias
- **Carboidratos**: 40-50% das calorias
- **Gordura**: 20-30% das calorias

## 📝 Estrutura do Projeto

```
Programa/
├── app.py                 # Aplicação Streamlit principal
├── requirements.txt       # Dependências Python
├── README.md              # Este arquivo
├── .github/               # Configurações do GitHub e Copilot
│   └── copilot-instructions.md
└── .gitignore             # Arquivos ignorados pelo Git
```

## 🔧 Desenvolvimento

Para adicionar novas funcionalidades:

1. Edite o arquivo `app.py`
2. Adicione novos imports conforme necessário
3. Teste a aplicação localmente com `streamlit run app.py`
4. Atualize `requirements.txt` se adicionar novas dependências

## 📊 Funcionalidades Futuras

- [ ] Integração com banco de dados persistente
- [ ] Sincronização com fitness trackers
- [ ] Recomendações de alimentos baseadas em IA
- [ ] Gráficos de evolução ao longo do tempo
- [ ] Suporte a diferentes dietas (keto, vegan, etc.)
- [ ] API para integração com outros apps

## 📧 Suporte

Para dúvidas ou sugestões sobre o aplicativo, entre em contato.

## 📄 Licença

Este projeto é fornecido como está para fins educacionais.

---

**Versão**: 2.0  
**Última atualização**: 2026-04-15  
**Desenvolvido com ❤️ para auxiliar nos estudos de nutrição**

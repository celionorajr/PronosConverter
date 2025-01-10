# Pronos Converter

Pronos Converter é uma aplicação desenvolvida em Python com PyQt5 para converter imagens no formato JPG para o formato DICOM e enviá-las para um servidor PACS.

## Funcionalidades

- Conversão de imagens JPG para o formato DICOM.
- Adição de informações do paciente ao arquivo DICOM.
- Envio dos arquivos DICOM para um servidor PACS.
- Interface gráfica moderna e intuitiva.
- Barra de progresso para acompanhar o processamento e envio das imagens.

## Captura de Tela

![Interface do Pronos Converter]([./screenshot.png](https://i.postimg.cc/5y1GBvRP/Captura-de-tela-2025-01-10-132506.png))

## Requisitos

- Python 3.8+
- Bibliotecas:
  - PyQt5
  - Pillow
  - pydicom
  - pynetdicom

## Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/celionorajr/PronosConverter.git
   cd pronos-converter
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure o arquivo `config.json` com as informações do PACS:
   ```json
   {
       "output_folder": "caminho/para/saida",
       "pacs": {
           "ip": "192.168.x.x",
           "port": 104,
           "ae_title": "NOME_AE"
       }
   }
   ```

## Uso

1. Execute o aplicativo:
   ```bash
   python main.py
   ```
2. Selecione a pasta contendo as imagens JPG.
3. Insira o nome do paciente (ou edite o preenchido automaticamente).
4. Clique em "Processar" para converter e enviar as imagens.

## Estrutura do Projeto

```
pronos-converter/
├── main.py              # Código principal
├── config.json          # Configuração do PACS
├── logo.png             # Logo exibida na interface
├── icon.png             # Ícone da aplicação
├── requirements.txt     # Dependências do projeto
├── README.md            # Documentação do projeto
└── screenshot.png       # Captura de tela da aplicação
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.



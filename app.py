import os
import fitz  # PyMuPDF para extrair texto do PDF
import openai
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'sent_docs'
openai.api_key = 'sua_chave_api_aqui'  # Substitua pela sua chave da OpenAI

# Rota para renderizar a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Função para salvar o PDF e extrair texto
def save_and_extract_text(pdf_file):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(file_path)
    
    with fitz.open(file_path) as pdf:
        text = ""
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text += page.get_text()
    return text

# Função para dividir o texto em partes menores
def split_text(text, max_tokens=2000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1
        if current_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = len(word) + 1
        current_chunk.append(word)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Função para consultar o modelo GPT da OpenAI
def query_openai_gpt(query, pdf_text_chunks):
    responses = []
    for chunk in pdf_text_chunks:
        prompt = f"{chunk}\n\nPergunta: {query}\nResposta:"
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0
        )
        response_text = response.choices[0].text.strip()
        if response_text:
            responses.append(response_text)
    
    return " ".join(responses) if responses else "Nenhuma resposta encontrada."

# Rota para processar o upload e consulta
@app.route('/process', methods=['POST'])
def process():
    if 'pdfFile' not in request.files or 'question' not in request.form:
        return jsonify({"error": "Arquivo PDF ou pergunta ausente"}), 400

    pdf_file = request.files['pdfFile']
    question = request.form['question']
    
    if pdf_file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400
    
    # Salvar e extrair texto do PDF
    text = save_and_extract_text(pdf_file)
    text_chunks = split_text(text)

    # Consultar o modelo da OpenAI
    answer = query_openai_gpt(question, text_chunks)
    
    return jsonify({"answer": answer})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)

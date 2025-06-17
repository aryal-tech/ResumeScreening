from flask import Flask, render_template, request
import PyPDF2
import math
from io import BytesIO

app = Flask(__name__)

# PDF to text
def extract_text_from_pdf(file_stream):
    reader = PyPDF2.PdfReader(file_stream)
    text = ''
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text

# TF-IDF functions
def preprocess(text):
    text = text.lower()
    return ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text).split()

def compute_tf(words):
    tf = {}
    total = len(words)
    for word in words:
        tf[word] = tf.get(word, 0) + 1
    for word in tf:
        tf[word] /= total
    return tf

def compute_idf(docs):
    idf = {}
    total_docs = len(docs)
    all_words = set(word for doc in docs for word in doc)

    for word in all_words:
        count = sum(1 for doc in docs if word in doc)
        idf[word] = math.log(total_docs / (1 + count))
    return idf

def compute_tfidf(tf, idf):
    return {word: tf[word] * idf[word] for word in tf}

def cosine_similarity(vec1, vec2):
    all_words = set(vec1.keys()).union(set(vec2.keys()))
    v1 = [vec1.get(w, 0.0) for w in all_words]
    v2 = [vec2.get(w, 0.0) for w in all_words]
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        jd_file = request.files['jd_file']
        resume_files = request.files.getlist('resume_files')

        # Extract and preprocess JD
        jd_text = extract_text_from_pdf(jd_file.stream)
        jd_words = preprocess(jd_text)

        # Extract and preprocess resumes
        resume_data = []
        resume_words_list = []
        for resume in resume_files:
            text = extract_text_from_pdf(resume.stream)
            words = preprocess(text)
            resume_data.append((resume.filename, words))
            resume_words_list.append(words)

        # TF-IDF
        all_docs = [jd_words] + resume_words_list
        tf_list = [compute_tf(doc) for doc in all_docs]
        idf = compute_idf(all_docs)
        tfidf_list = [compute_tfidf(tf, idf) for tf in tf_list]

        jd_tfidf = tfidf_list[0]
        resume_tfidfs = tfidf_list[1:]

        for (filename, _), tfidf in zip(resume_data, resume_tfidfs):
            score = cosine_similarity(jd_tfidf, tfidf)
            results.append((filename, score))

        results.sort(key=lambda x: x[1], reverse=True)

    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)

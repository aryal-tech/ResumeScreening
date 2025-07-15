import regex as re
from core.extract import get_job_text, get_resume_texts
from database.db_connect import insert_document

# ----------------------------------------------------------------------
# Define stop words
# ----------------------------------------------------------------------
stop_words = {
    'the', 'i', 'is', 'in', 'and', 'to', 'has', 'that', 'of', 'a', 'using',
    'an', 'on', 'for', 'with', 'it', 'as', 'this', 'by', 'be', 'are',
    'was', 'were', 'at', 'from', 'or', 'but', 'not', 'have', 'had',
    'which', 'they', 'their', 'you', 'your', 'we', 'he', 'she', 'his',
    'her', 'them', 'our', 'out', 'can'
}.union({
    'experience', 'skills', 'responsible', 'proficient', 'knowledge',
    'ability', 'expertise', 'team', 'member', 'years', 'work',
    'career', 'job', 'role', 'organization', 'position', 'seeking',
    'objective', 'summary', 'professional', 'dedicated', 'motivated',
    'hardworking', 'results', 'oriented', 'goal', 'driven', 'strong',
    'excellent', 'communication', 'interpersonal', 'detail', 'focused',
    'resume', 'cv', 'well', 'problem', 'solving', 'fast', 'paced',
    'environment', 'adaptable', 'flexible', 'multiple', 'tasks',
    'effective', 'efficient', 'self', 'starter', 'dependable',
    'references', 'available', 'upon', 'request', 'apply', 'making',
    'enthusiast'
})

# ----------------------------------------------------------------------
# Manual tokenizer that preserves tech terms like C++, C#, .NET, CI/CD
# ----------------------------------------------------------------------
def tokenize(text: str):
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789+#./-")
    tokens, word = [], ''
    for char in text:
        if char in allowed_chars:
            word += char
        else:
            if word:
                tokens.append(word)
                word = ''
    if word:
        tokens.append(word)
    return tokens

# ----------------------------------------------------------------------
# Lemmatization function with custom exceptions
# ----------------------------------------------------------------------
def lemmatization(word: str):
    exception = {
        # General irregular forms
        "men": "man", "women": "woman", "children": "child",
        "mice": "mouse", "geese": "goose", "feet": "foot", "teeth": "tooth",

        # Verb normalization (past tense → base form)
        "ran": "run", "went": "go", "studies": "study", "studied": "study",
        "led": "lead", "wrote": "write", "written": "write",
        "built": "build", "made": "make", "held": "hold",
        "taught": "teach", "understood": "understand", "performed": "perform",
        "developed": "develop", "analyzed": "analyze", "evaluated": "evaluate",
        "managed": "manage", "created": "create", "designed": "design",
        "implemented": "implement", "organized": "organize",
        "collaborated": "collaborate", "conducted": "conduct",
        "optimized": "optimize", "presented": "present",
        "achieved": "achieve", "deployed": "deploy", "aspiring": "aspire"
    }

    if word in exception:
        return exception[word]

    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    elif word.endswith("ing") and len(word) > 4:
        return word[:-3]
    elif word.endswith("ed") and len(word) > 3:
        return word[:-2] + "e"
    elif word.endswith("es") and len(word) > 3:
        return word[:-2]
    elif word.endswith("s") and len(word) > 3:
        return word[:-1]

    return word

# ----------------------------------------------------------------------
# Preprocessing: lowercase, clean, tokenize, lemmatize, remove stopwords
# ----------------------------------------------------------------------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\+\#\.\-/]', ' ', text)
    tokens = tokenize(text)
    processed = [lemmatization(w) for w in tokens if w not in stop_words]
    return " ".join(processed)

# ----------------------------------------------------------------------
# Orchestrator: process job and resumes, store in DB
# ----------------------------------------------------------------------
def final_text():
    job_text = get_job_text()
    cleaned_job_desc = preprocess_text(job_text)
    print("\nCleaned Job Description:\n", cleaned_job_desc[:500])
    insert_document("Job_Description", "job", job_text, cleaned_job_desc)

    resume_raw_list = get_resume_texts()
    for idx, resume_raw in enumerate(resume_raw_list, start=1):
        cleaned = preprocess_text(resume_raw)
        filename = f"Resume_{idx}"
        insert_document(filename, "resume", resume_raw, cleaned)

    return job_text

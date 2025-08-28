import regex as re

# Compound replacements
COMPOUND_TERMS = {
    'c++': 'cpp_language',
    'c#': 'csharp_language',
    '.net': 'dotnet_framework',
    'ci/cd': 'cicd_pipeline',
    'ci-cd': 'cicd_pipeline',
    'data science': 'data_science',
    'machine learning': 'machine_learning',
    'node.js': 'nodejs',
    'git': 'git',
    'github': 'github_platform',
    'html5': 'html5'
}

# Manual synonym normalization for resume domain
SYNONYM_MAP = {
    'developed': 'build',
    'created': 'build',
    'built': 'build',
    'designed': 'design',
    'implemented': 'implement',
    'executed': 'implement',
    'managed': 'lead',
    'led': 'lead',
    'supervised': 'lead',
    'analyzed': 'analyze',
    'examined': 'analyze',
    'evaluated': 'analyze',
    'deployed': 'launch',
    'released': 'launch',
    'teamwork': 'collaboration',
    'collaborated': 'collaboration',
    'coordinated': 'collaboration',
    'achieved': 'accomplish',
    'accomplished': 'accomplish',
    'resolved': 'solve',
    'fixed': 'solve',
    'troubleshot': 'solve'
}

def preserve_compounds(text):    
    terms_sorted = sorted(COMPOUND_TERMS, key=len, reverse=True)
    for term in terms_sorted:
        text = re.sub(r'(?i)\b{}\b'.format(re.escape(term)), COMPOUND_TERMS[term], text)
    return text

stop_words = {
    'the', 'i', 'is', 'in', 'and', 'to', 'has', 'that', 'of', 'a', 'using',
    'an', 'on', 'for', 'with', 'it', 'as', 'this', 'by', 'be', 'are',
    'was', 'were', 'at', 'from', 'or', 'but', 'not', 'have', 'had',
    'which', 'they', 'their', 'you', 'your', 'we', 'he', 'she', 'his',
    'her', 'them', 'our', 'out', 'can',
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
}

def tokenize(text: str):
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789_")
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

def lemmatization(word: str):
    exception = {
        "men": "man", "women": "woman", "children": "child",
        "mice": "mouse", "geese": "goose", "feet": "foot", "teeth": "tooth",
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

def normalize_synonyms(word: str):
    return SYNONYM_MAP.get(word, word)

def preprocess_text(text: str):
    text = text.lower()
    text = preserve_compounds(text)
    text = re.sub(r'[^a-z0-9_\s]', ' ', text)
    tokens = tokenize(text)
    processed = [
        normalize_synonyms(lemmatization(w))
        for w in tokens if w not in stop_words
    ]
    return " ".join(processed)

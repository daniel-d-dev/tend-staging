import re
from sentence_transformers import SentenceTransformer

# clear, unambiguous expressions of crisis-level distress. They are deliberately narrow and severe, since this is meant to be an unconditional escalation to high distress, not a general having a hard time detector, which the baseline-deviation trend rules already cover. Covers constructs from suicidology literature. There are a few different phrasings for each construct so that its not just tuned to one exact wording
CRISIS_REFERENCE = [
    "I feel completely hopeless",
    "Everything feels like too much to handle",
    "I can't cope with this anymore",
    "I feel like I'm drowning",
    "I don't see the point in anything anymore",
    "I feel completely overwhelmed",
    "I can't take this anymore",
    "I feel like giving up",
    "Nothing feels like it will get better",
    "I feel trapped and there's no way out",
    "I'm really struggling to keep going",
    "I feel like I'm at breaking point",
    "Everyone would be better off without me", # burden-relief
    "I feel like a burden to everyone around me", # burden-relief
    "No one would notice if I was gone", # thwarted belongingness
    "I don't think anyone would care if I disappeared", # thwarted belongingness
    "I want to hurt myself", # self-harm urges
    "I have urges to hurt myself", # self-harm urges
    "I want to say goodbye before it's too late", # farewell-adjacent
    "Thank you for everything, in case I don't get another chance", # farewell-adjacent
    "I should tell the people I care about how much they mean to me, before it's too late", # farewell-adjacent
    "I've stopped fighting it, whatever happens now just happens", # defeat
    "I don't have any fight left in me", # defeat
    "I can't picture where I'll be next year", # no-future orientation
    "I can't imagine having any future", # no-future orientation
    "I wish I wouldn't wake up in the morning", # passive ideation
    "I don't want to open my eyes tomorrow", # passive ideation
    "I was lying there hoping I would not have to wake up tomorrow", # passive ideation
    "I need to leave everything behind and start over somewhere new", # escape framing
    "I just need to get away from all of this", # escape framing
    "I just want to disappear", # wanting to disappear
    "I want to stop existing", # wanting to disappear
    "I'm so tired of pretending everything is fine", # masking
    "I can't keep pretending I'm okay", # masking
    "I hate who I am", # self-hatred/worthlessness
    "I don't deserve anything good", # self-hatred/worthlessness
    "I feel sick with guilt and can't live with it", # acute shame/guilt
    "The guilt is unbearable", # acute shame/guilt
    "I don't know how I'm going to face tomorrow", # can't-face-another-day
    "I don't think I can face another day", # can't-face-another-day
    "I feel like I am watching myself from outside my own body", # dissociation
    "Everything feels unreal lately, like none of this is really happening to me", # dissociation
    "I have been drinking a lot more than I should just to get through the evenings", # substance-coping escalation
    "I have been leaning on drinks most nights to switch my brain off", # substance-coping escalation
    "I need help", # explicit help-seeking
    "I really need help right now", # explicit help-seeking
]

# ordinary difficulty language that shouldn't trigger the safety net. Contrastive reference set to weigh crisis phrases against
MODERATE_REFERENCE = [
    "I'm having a tough day",
    "I'm feeling a bit stressed",
    "I'm a little tired today",
    "It's been an okay day",
    "I'm managing okay",
    "Today was fine",
    "I feel good today",
    "I'm a bit worried about something",
    "I'm feeling a little low",
    "It's been a long week",
]

model = SentenceTransformer("all-mpnet-base-v2")
crisis_ref = model.encode(CRISIS_REFERENCE)
moderate_ref = model.encode(MODERATE_REFERENCE)

MAX_CHUNK_WORDS = 30
# words a run-on message with no punctuation naturally pauses at anyway. This is preferred over a hard word count cut, since chopping mid-clause can make an ordinary bit of text look alarming just from being cut off badly, not from anything it actually says
CLAUSE_BREAK = re.compile(r",\s+|\s+(?:but|so|and then|anyway|also|honestly|because)\s+")

# a short sentence can still be two separate thoughts joined by a comma, like "today was awful, I need help." Scoring that as one chunk waters down the second half enough that it can go unnoticed. So short sentences are also checked for a comma split, but only kept if every piece that comes out is this short too, since longer comma-joined clauses usually rely on each other to make sense (a hypothetical, a "but actually I'm fine" sort of thing) and splitting those apart can make an otherwise harmless sentence look alarming
SHORT_CLAUSE_CAP = 5

# some run-ons have no comma or pause word at all, so even that fallback sometimes still needs a hard word count cut. this nudges the cut forward past any word that would leave the clause hanging (things like "the" "a" "who" "and" etc) so it lands somewhere that actually reads as complete instead of stopping mid-thought
DANGLES_IF_CUT_AFTER = {
    "a", "an", "the", "at", "in", "on", "to", "of", "for", "with", "and", "or", "but",
    "who", "which", "that", "when", "while", "after", "before", "since", "now", "so",
    "as", "if", "my", "your", "his", "her", "their", "our", "its", "i",
}

def split_sentences(text: str) -> list[str]: # splits on punctuation and newlines, then falls back to clause boundaries and finally a hard word count window for anything still too long. needed because a lowercase, punctuation-free message (which is the way people usually actually write when texting, especially on phones) would otherwise collapse into one really long sentence and dilute a crisis line buried inside it
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    pieces = [p.strip() for p in pieces if p.strip()]
    chunks = []
    for piece in pieces:
        words = piece.split()
        if len(words) <= MAX_CHUNK_WORDS:
            chunks.append(piece)
            short_clauses = [c.strip() for c in CLAUSE_BREAK.split(piece) if c.strip()]
            if len(short_clauses) > 1 and all(len(c.split()) <= SHORT_CLAUSE_CAP for c in short_clauses):
                chunks.extend(short_clauses) # added alongside the whole piece above not instead of it so a message that already scored correctly can't start scoring lower
        else:
            clauses = [c.strip() for c in CLAUSE_BREAK.split(piece) if c.strip()]
            for clause in clauses:
                clause_words = clause.split()
                if len(clause_words) <= MAX_CHUNK_WORDS:
                    chunks.append(clause)
                else:
                    # last resort. No natural pause point either, so cut hard and nudge past dangling words
                    i = 0
                    while i < len(clause_words):
                        end = min(i + MAX_CHUNK_WORDS, len(clause_words))
                        while end < len(clause_words) and clause_words[end - 1].lower().strip(".,!?\"'") in DANGLES_IF_CUT_AFTER:
                            end += 1
                        chunks.append(" ".join(clause_words[i:end]))
                        i = end
    return chunks

def score_crisis_language_per_sentence(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return -1.0 # empty/whitespace-only text. Nothing to score, return a value safely below the threshold rather than crash
    embeddings = model.encode(sentences)
    crisis_scores = (embeddings @ crisis_ref.T).max(axis = 1)
    moderate_scores = (embeddings @ moderate_ref.T).max(axis = 1)
    per_sentence = crisis_scores - moderate_scores
    return float(per_sentence.max()) # the single most alarming sentence decides the score, not the average

# calibrated against a labeled dataset of real and mundane examples. I picked a value with real margin below where recall actually starts dropping, not the edge of what happened to work on one sample. a false negative here is a missed crisis, a false positive is an unwarranted but harmless nudge, so the margin deliberately favours catching more
CRISIS_THRESHOLD = 0.16

def is_crisis_language(text: str) -> bool:
    return score_crisis_language_per_sentence(text) > CRISIS_THRESHOLD
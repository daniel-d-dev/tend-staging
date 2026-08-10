import uuid
from app.services.crisis_safety_net import model as embedding_model

CONTRAST_SEEDS = { # each of these is a real hand-written crisis scenario that gets rewritten 4 ways in build_labelling_batch.py. the more distinct scenarios covered here, the more the dataset actually proves, since 4 rewrites of the same seed only really test one scenario, not 4. seed_1/seed_2 are simple direct statements, and every seed from seed_3 onward is a genuinely new scenario rather than a rephrasing of an earlier one
    "seed_1": "I feel completely overwhelmed and hopeless right now, like everything is too much to handle.",
    "seed_2": "I just feel like I am completely done with everything, I cannot keep going like this.",
    "seed_3": "I feel like such a burden to everyone around me, and it would be easier for them if I wasn't here.", # feeling like a burden to others, distinct from anything the other seeds cover
    "seed_4": "I just want to disappear and not have to deal with any of this anymore.", # wanting to escape, distinct from "no point in anything"
    "seed_5": "I feel completely empty inside, like there's nothing left of me anymore.", # numbness/emptiness, distinct from "overwhelmed" (absence of feeling, not excess of it)
    "seed_6": "I don't know how to make this stop, I can't see any way out of this.", # trapped/no-way-out framing, distinct from hopelessness generally
    "seed_7": "I'm so tired of pretending everything is fine when it really isn't.", # masking/camouflaging - a real person types like this even when hiding how bad things are
    "seed_8": "I'm so exhausted from just trying to survive each day that I don't have anything left to give.", # exhaustion-from-bare-survival, distinct from generic "can't cope"

    # thwarted belongingness / isolation
    "seed_9": "Honestly, I don't think anyone would even notice if I just wasn't around anymore.",
    "seed_10": "Nobody's really checked in on me in weeks, it's like I could disappear and it wouldn't change anything for anyone.",
    "seed_11": "Been stuck at home most of this week with how unwell I've been feeling, and honestly not sure anyone would notice either way.",

    # defeat
    "seed_12": "I've stopped fighting it, whatever happens now just happens, I don't have any fight left in me.",
    "seed_13": "Consultant went through the options again today. I think I'm done fighting this, whatever comes next just comes.",
    "seed_14": "Another red letter today. Not even going to try and sort it out this time, I've lost this one and I'm done pretending otherwise.",

    # hopelessness about change (distinct from general hopelessness)
    "seed_15": "Nothing is ever going to get better, this is just how things are going to be from now on.",
    "seed_16": "Doctor says it's manageable long-term. I just can't see it ever actually being different.",
    "seed_17": "Another weekend with no plans, no one really to call. Some days I think this is just permanently how my life looks now, and it's never going to change.",

    # passive ideation / wish to not wake up
    "seed_18": "Some nights I just wish I wouldn't wake up in the morning.",
    "seed_19": "I've caught myself hoping I just wouldn't have to open my eyes tomorrow, if I'm honest.",
    "seed_20": "Rough one at work again. Lay there for ages tonight kind of hoping I just wouldn't have to wake up for it tomorrow.",

    # escape framing (distinct from "wanting to disappear" - escape as the only solution)
    "seed_21": "The only way I can see to fix this is to just leave everything behind and start over somewhere no one knows me.",
    "seed_22": "If I could just get away from here completely, maybe none of this would follow me anymore.",
    "seed_23": "Another scan booked in for next month. Keep thinking if I could just get away from all of it - the appointments, the waiting - none of it would matter anymore.",

    # no-future orientation
    "seed_24": "I can't picture where I'll be next year, it's like there's nothing there when I try to imagine it.",
    "seed_25": "Everyone's talking about next term like it's a given. I genuinely can't picture myself in it.",
    "seed_26": "Filled in a form today that asked about five-year plans. Just left it blank, couldn't picture that far ahead even a little.",

    # sudden-calm/resolution - PRIORITY, predicted blind spot (the detector likely reads this as positive)
    "seed_27": "I feel strangely calm now, like everything's finally decided and I don't have to worry anymore.",
    "seed_28": "Weirdly, today's the first day in ages I've actually felt at peace. Everything just feels sorted now.",
    "seed_29": "Handed in my notice today. Feels really peaceful actually, like a weight's finally lifted and it's all settled.",
    "seed_30": "Sorted through some of my things today, gave a few bits away. Felt oddly relieved doing it, like things are finally simple.",

    # burden-relief framing - PRIORITY, predicted blind spot (distinct from perceived burdensomeness)
    "seed_31": "Everyone would probably be better off without me around causing them so much stress.",
    "seed_32": "Mum's been so worn out looking after me lately. Honestly think she'd get a break if I wasn't around to worry about.",
    "seed_33": "Had a good chat with my flatmate today about splitting bills. Made me think they'd probably be better off with someone else around, less of a drain on things.",
    "seed_34": "My partner deserves so much better than dealing with me, they'd be so much happier without this weighing them down.",

    # farewell-adjacent language
    "seed_35": "Just wanted to say thank you for everything, in case I don't get the chance to later.",
    "seed_36": "Been thinking about people I should really tell how much they mean to me, before it's too late to say it.",
    "seed_37": "Sorted out some old photos today, sent a few to old friends with a little note. Felt important to say the things I hadn't said.",

    # self-hatred / worthlessness
    "seed_38": "I hate who I am, I don't think I deserve anything good happening to me.",
    "seed_39": "Failed again. Honestly I don't know why I even bother, I'm just not worth the effort people put into me.",
    "seed_40": "Missed the bus again today, stupid mistake. Feels about right honestly, I mess up everything I touch.",

    # acute shame / guilt
    "seed_41": "I can't stop thinking about what I did, I feel sick with guilt and I don't know how to live with it.",
    "seed_42": "Still can't shake what happened between us. The guilt is honestly unbearable most days.",
    "seed_43": "Quiet day, mostly just sat with how ashamed I feel about everything lately, couldn't really focus on much else.",

    # dissociation
    "seed_44": "I feel like I'm watching myself from outside my body, like none of this is really happening to me.",
    "seed_45": "Everything's felt kind of unreal lately, like I'm walking through someone else's life instead of my own.",
    "seed_46": "Sat through the whole meeting today but it felt like I was watching it from somewhere outside myself, hard to explain.",

    # can't-face-another-day desperation
    "seed_47": "I don't know how I'm going to face getting up and doing this all again tomorrow.",
    "seed_48": "Another round of treatment tomorrow. Honestly don't know where I'm going to find it in me to face it.",
    "seed_49": "Alarm's set for 6 again. Just lying here dreading it, don't know how many more of these days I've got in me.",

    # self-harm urges, distinct from suicidality
    "seed_50": "I've been having urges to hurt myself again, just to feel something different.",
    "seed_51": "Been getting that pull again to hurt myself, haven't acted on it but it's there most days now.",
    "seed_52": "Stressful day, felt that familiar urge again to hurt myself, been managing to distract myself from it so far.",

    # substance-coping escalation
    "seed_53": "I've been drinking a lot more just to get through the evenings lately, more than I should.",
    "seed_54": "Work's been brutal, been leaning on a few drinks most nights just to switch my brain off.",
    "seed_55": "Quiet one today, just had a fair few drinks again tonight, seems to be becoming more of a nightly thing than I'd like.",
}

SPLICE_SENTENCES = {
    "splice_a": "I am not sure how much longer I can keep pretending I am fine.",
    "splice_b": "I feel like I am drowning and I do not know how to ask for help.",
    "splice_c": "Honestly I do not see the point in any of this any more.",
}

seed_embeddings = {} # one embedding per seed, worked out once up front so nearest_seed doesn't have to redo this every time it's called
for group_id, sentence in CONTRAST_SEEDS.items():
    seed_embeddings[group_id] = embedding_model.encode([sentence])[0] # encode() expects a list of texts and returns a list of embeddings even for one sentence, so this wraps the sentence in a list going in and pulls the single result back out with [0]

def nearest_seed(text: str) -> str: # contrast transforms are asked to "keep as much of the original wording as possible" but sometimes drift far from it, comparing embeddings catches a drifted rewrite that plain keyword matching would miss
    text_embedding = embedding_model.encode([text])[0]
    scores = {}
    for group_id, seed_emb in seed_embeddings.items():
        scores[group_id] = float(text_embedding @ seed_emb)

    best_group_id = None
    best_score = None
    for group_id, score in scores.items():
        if best_score is None or score > best_score:
            best_group_id = group_id
            best_score = score
    return best_group_id

def assign_group_id(source: str, text: str, known_group_id: str | None = None) -> str: # if you already know which seed this text actually came from, pass it as known_group_id and this just hands it straight back, that's what build_labelling_batch.py does for contrast/spliced rows, since it already knows. otherwise this falls back to guessing with nearest_seed, which isn't fully reliable
    if known_group_id is not None:
        return known_group_id
    if source.startswith("contrast:"):
        for group_id, sentence in CONTRAST_SEEDS.items():
            if text.strip() == sentence.strip():
                return group_id
        return nearest_seed(text)
    if source.startswith("spliced:"):
        for group_id, sentence in SPLICE_SENTENCES.items():
            if sentence in text:
                return group_id
        return "splice_unknown" # shouldn't happen, better to flag it clearly than quietly assign it to the wrong group
    return f"solo_{uuid.uuid4().hex[:8]}" # grid candidates aren't derived from a shared seed, so each just gets its own random, unique group id

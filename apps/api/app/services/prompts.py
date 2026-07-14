from datetime import date

PROMPTS = [
    "What's been taking up most of your headspace today, and where are you at with it?",
    "How connected have you felt to the people around you lately, and what's shaped that?",
    "What's something that's gone well for you recently, and how did it feel?",
    "How have your energy levels been lately, and what do you think has been driving that?",
    "What's something you've been putting off lately, and what's making it feel difficult?",
    "How has your sleep been lately, and how has it been affecting how you feel day to day?",
    "What's something small that brought you a bit of comfort today, and why do you think it helped?",
    "What's been making you feel most anxious or unsettled lately, and how are you sitting with that?",
    "How easy has it been to switch off and relax lately - what tends to get in the way?",
    "What's been worrying you most lately, and how much has it been getting to you?",
    "How much have you been enjoying the things you usually like doing, and what do you think has been behind that?",
    "How have things been feeling emotionally lately — have there been moments where things felt a bit heavier than usual?",
    "How motivated have you felt to get things done today, and what's been getting in the way, if anything?",
    "How supported have you felt by the people around you today, and what's that been like?",
    "How well have you felt understood by the people around you lately, and what's shaped that feeling?",
    "What's something you've been carrying lately that you haven't quite managed to say to anyone?",
    "How have your interactions with others been feeling recently, and what's been making them feel that way?",
    "How in control have you felt of the things going on in your life recently, and what's been contributing to that?",
    "What's felt most overwhelming or difficult to manage lately, and how are you dealing with it?",
    "How much time have you had to yourself lately, and how has the pace of things been feeling?",
    "How has your body been feeling — any tension, tiredness, or aches today?",
    "How has your focus been today — if your mind has been wandering, what's it been drawn to?",
    "What's been going round in your head lately that you can't quite let go of?",
    "How have you been treating yourself lately — have you been giving yourself much grace, or have you been a bit hard on yourself?",
    "How much have you felt like yourself lately, and what do you think has been behind that?",
    "What's something that gave you a sense of purpose or meaning recently?",
    "What moments today have felt genuinely okay, or even good — what made them feel that way?",
    "What's something you've done recently that felt like properly looking after yourself, and how did it feel?",
    "How are you feeling about what's coming up for you, and what's on your mind about it?",
    "What's one thing that's made today feel worthwhile, even in a small way?",
]

def get_todays_prompt() -> str:
    day_number = date.today().toordinal() # days passed since the 1st of Jan 0001, increments by 1 each day
    index = day_number % len(PROMPTS) # remainder after dividing by list length, goes through list and back to the start
    return PROMPTS[index]
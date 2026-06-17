from datetime import date

PROMPTS = [
    "What's been the main thing on your mind today?",
    "How connected have you felt to the people around you lately?",
    "What's one thing that went well for you recently?",
    "How would you describe your energy levels over the past day or so?",
    "Is there anything you've been putting off that's weighing on you?",
    "How have you been sleeping recently?",
    "What's something small that brought you a bit of comfort today?"
]

def get_todays_prompt() -> str:
    day_number = date.today().toordinal() # days passed since the 1st of Jan 0001, increments by 1 each day
    index = day_number % len(PROMPTS) # remainder after dividing by list length, goes through list and back to the start
    return PROMPTS[index]
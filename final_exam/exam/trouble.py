'''
The backend for the double trouble game.
'''

# Put any global variables your implementation needs here
pile = {}
card_id = 0

def flip_card(card_obj):
    '''
    Takes in a card_obj which is a python dictionary consistsing of two keys:
     suit: Either "Hearts", "Spades", "Diamonds", or "Clubs"
     number: '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'J', 'Q', 'K'

    E.G. {"suit": "Hearts", "number": "5"}

    This card is then added to the pile.

    If the card already exists in the pile, it will not be added.
    '''
    global card_id
    for s in card_obj['suit']:
        for n in card_obj['numer']:
            pile[card_id] = {"suit": s, "number": n}
            card_id = card_id + 1

def is_double_trouble():
    '''
    Returns true if the last two cards were the same number. False otherwise.
    If this function is called whilst true, the pile is reset to empty.
    '''
    x1 = list(reversed(list(pile)))[0]
    x2 = list(reversed(list(pile)))[1]
    if x1 == x2:
        return True
    else:
        return False

def is_trouble_double():
    '''
    Returns true if the last four cards had the same suit. False otherwise.
    If this function is called whilst true, the pile is reset to empty.
    '''
    pass

def is_empty():
    '''
    Returns a boolean that is true if the pile of cards is empty, false if it is not empty
    '''
    if len(pile) == 0:
        return True
    else:
        return False

def clear():
    '''
    Clears the pile and resets the game
    '''
    global pile
    pile = {}
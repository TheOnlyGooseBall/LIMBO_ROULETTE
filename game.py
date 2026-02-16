
import sys
import random

def clear():
    print("\n" * 40)

def clamp(val, low, high):
    return max(low, min(high, val))

def nerve_label(n):
    if n > 70: return "STABLE"
    if n > 30: return "SHAKY"
    return "COLLAPSING"

def generate_shells(round_num):
    base = random.choice([4,5,6])
    base += round_num  
    pool = []

    for _ in range(base):
        roll = random.random()
        if roll < 0.35:
            pool.append("live")
        elif roll < 0.65:
            pool.append("blank")
        elif roll < 0.85:
            pool.append("fuse_2")
        else:
            pool.append("fuse_3")

    random.shuffle(pool)
    return pool


def update_psychology(state):
    print(f"\n[ NERVE: {state['player_nerve']}/{state['max_nerve']} | {nerve_label(state['player_nerve'])} ]")

    expired = []

    for i, fuse in enumerate(state['active_fuses']):
        fuse["timer"] -= 1
        state["player_nerve"] -= 5
        print(f"-> Fuse ticking... {fuse['timer']} turns left")

        if fuse["timer"] <= 0:
            expired.append(i)

    for i in reversed(expired):
        print("\n[ !!! FUSE DETONATED !!! ]")
        state["player_health"] -= 2
        state["player_nerve"] -= 20
        state["active_fuses"].pop(i)

    state["player_nerve"] = clamp(state["player_nerve"], 0, state["max_nerve"])


def give_items(state, round_num):
    items = ["pills", "mirror", "pliers"]
    state["player_items"] = random.sample(items, k=min(2, len(items)))

def use_item(state):
    print("Items:", state["player_items"])
    choice = input("Use which item? ").strip().lower()

    if choice not in state["player_items"]:
        print("Invalid item.")
        return False

    if choice == "pills":
        heal = 15
        state["player_nerve"] += heal
        print("You steady your breathing.")
    elif choice == "mirror":
        if state["shell_list"]:
            print("Next shell glimpse:", state["shell_list"][0])
        else:
            print("Nothing loaded.")
    elif choice == "pliers":
        if state["active_fuses"]:
            print("You rip a fuse off your chest.")
            state["active_fuses"].pop(0)
            state["player_nerve"] -= 10
        else:
            print("No fuse to remove.")

    state["player_items"].remove(choice)
    state["player_nerve"] = clamp(state["player_nerve"], 0, state["max_nerve"])
    return True

def player_turn(state):

    update_psychology(state)
    if state["player_health"] <= 0:
        return False

    flip = False
    hallucinate = False

    if state["player_nerve"] < 30 and random.random() < 0.2:
        flip = True

    if state["player_nerve"] < 20 and random.random() < 0.25:
        hallucinate = True

    print(f"\nYOUR TURN | HP:{state['player_health']} Dealer:{state['dealer_health']}")

    if hallucinate:
        fake = random.choice(["live","blank","fuse_2"])
        print(f"[You think the next shell is: {fake}]")

    choice = input("(S)hoot or (I)tem? ").strip().upper()

    if choice == "I":
        if not state["player_items"]:
            print("No items.")
            return True
        use_item(state)
        return True

    if not state["shell_list"]:
        return False

    target = input("Shoot (D)ealer or (S)elf? ").strip().upper()

    if flip:
        target = "S" if target == "D" else "D"
        print("[Your hand slips.]")

    shell = state["shell_list"].pop(0)

    if target == "S":
        if shell == "live":
            print("BANG. You shot yourself.")
            state["player_health"] -= 1
            state["player_nerve"] -= 20
            return False
        elif "fuse" in shell:
            timer = int(shell.split("_")[1])
            print(f"Fuse attached. {timer} turns.")
            state["active_fuses"].append({"timer": timer})
            state["player_nerve"] -= 15
            return False
        else:
            print("Blank. Relief.")
            state["player_nerve"] += 10
            return True

    else:
        if shell == "live":
            print("Dealer hit.")
            state["dealer_health"] -= 1
        elif "fuse" in shell:
            if random.random() < 0.5:
                print("Fuse sticks to Dealer.")
                state["dealer_fuse"] = int(shell.split("_")[1])
            else:
                print("Fuse falls uselessly.")
        else:
            print("Blank.")

        return False

def dealer_turn(state):

    print("\nDEALER TURN")

    if state.get("dealer_fuse"):
        state["dealer_fuse"] -= 1
        print("Dealer fuse ticking...")

        if state["dealer_fuse"] <= 0:
            print("Dealer explodes.")
            state["dealer_health"] -= 2
            state["dealer_fuse"] = None

    if not state["shell_list"]:
        return

    shell = state["shell_list"].pop(0)

    if shell == "live":
        print("Dealer shoots you.")
        state["player_health"] -= 1
        state["player_nerve"] -= 20
    elif "fuse" in shell:
        print("Dealer forces fuse onto you.")
        timer = int(shell.split("_")[1])
        state["active_fuses"].append({"timer": timer})
        state["player_nerve"] -= 10
    else:
        print("Dealer fires blank.")


def key_trial(state):

    print("\nFINAL DOOR")

    nerve = state["player_nerve"]

    if nerve >= 70:
        keys = 3
    elif nerve >= 40:
        keys = 4
    elif nerve >= 10:
        keys = 5
    else:
        keys = 6

    correct = random.randint(1, keys)
    attempts = 3

    while attempts > 0:
        print(f"Keys: {keys} | Attempts: {attempts}")
        try:
            pick = int(input("Pick key: "))
        except:
            attempts -= 1
            continue

        if pick == correct:
            print("The door opens. You escape LIMBO.")
            return True
        else:
            print("Wrong. The keys reshuffle.")
            state["player_nerve"] -= 15
            attempts -= 1
            correct = random.randint(1, keys)

    print("You remain in Limbo.")
    return False


def play_game():

    name = input("Sign the waiver. Name: ")

    state = {
        "player_name": name,
        "player_health": 4,
        "dealer_health": 4,
        "player_nerve": 75,
        "max_nerve": 100,
        "active_fuses": [],
        "dealer_fuse": None,
        "shell_list": [],
        "player_items": []
    }

    for round_num in range(1,4):

        print(f"\n=== ROUND {round_num} ===")
        give_items(state, round_num)
        state["shell_list"] = generate_shells(round_num)

        turn = True

        while state["player_health"] > 0 and state["dealer_health"] > 0:

            if not state["shell_list"]:
                state["shell_list"] = generate_shells(round_num)

            if turn:
                turn = player_turn(state)
            else:
                dealer_turn(state)
                turn = True

        if state["player_health"] <= 0:
            print("You died in Limbo..... PLAY AGAIN?")
            return

        print("Dealer defeated.")
        state["dealer_health"] += 2
        state["max_nerve"] -= 10  # permanent decay
        state["player_nerve"] = clamp(state["player_nerve"],0,state["max_nerve"])

    print("\nThe shells stop. The door remains.")
    key_trial(state)




play_game()

import random

# ------------------ CORE UTILS ------------------

def clamp(val, low, high):
    return max(low, min(high, val))


def nerve_label(n):
    if n > 70:
        return "STABLE"
    if n > 30:
        return "SHAKY"
    return "COLLAPSING"


# ------------------ SHELL SYSTEM ------------------

def generate_shells(round_num, difficulty):
    base = random.choice([4, 5, 6]) + round_num
    pool = []

    # Difficulty shifts probability toward live shells
    live_bias = 0.30 + (difficulty * 0.05)
    fuse_bias = 0.20 + (difficulty * 0.03)

    for _ in range(base):
        roll = random.random()
        if roll < live_bias:
            pool.append("live")
        elif roll < live_bias + 0.30:
            pool.append("blank")
        elif roll < live_bias + 0.30 + fuse_bias:
            pool.append("fuse_2")
        else:
            pool.append("fuse_3")

    random.shuffle(pool)
    return pool


# ------------------ PSYCHOLOGY ------------------

def update_psychology(state):
    print(f"\n[ NERVE: {state['player_nerve']}/{state['max_nerve']} | {nerve_label(state['player_nerve'])} ]")

    expired = []

    for i, fuse in enumerate(state["active_fuses"]):
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


# ------------------ ITEMS ------------------

def give_items(state):
    items = ["pills", "mirror", "pliers"]
    state["player_items"] = random.sample(items, 2)


def use_item(state):
    if not state["player_items"]:
        print("No items.")
        return True

    print("Items:", state["player_items"])
    choice = input("Use which item? ").strip().lower()

    if choice not in state["player_items"]:
        print("Invalid item.")
        return True

    if choice == "pills":
        state["player_nerve"] += 15
        print("You steady your breathing.")

    elif choice == "mirror":
        if state["shell_list"]:
            print("Next shell glimpse:", state["shell_list"][0])
        else:
            print("Nothing loaded.")

    elif choice == "pliers":
        if state["active_fuses"]:
            print("You rip a fuse off.")
            state["active_fuses"].pop(0)
            state["player_nerve"] -= 10
        else:
            print("No fuse to remove.")

    state["player_items"].remove(choice)
    state["player_nerve"] = clamp(state["player_nerve"], 0, state["max_nerve"])
    return True


# ------------------ PLAYER TURN ------------------

def player_turn(state):
    update_psychology(state)

    if state["player_health"] <= 0:
        return False

    flip = state["player_nerve"] < 30 and random.random() < 0.2
    hallucinate = state["player_nerve"] < 20 and random.random() < 0.25

    print(f"\nYOUR TURN | HP:{state['player_health']} Dealer:{state['dealer_health']} Difficulty:{state['difficulty']}")

    if hallucinate:
        fake = random.choice(["live", "blank", "fuse_2"])
        print(f"[You think the next shell is: {fake}]")

    choice = input("(S)hoot or (I)tem? ").strip().upper()

    if choice == "I":
        return use_item(state)

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
        elif "fuse" in shell:
            timer = int(shell.split("_")[1])
            print(f"Fuse attached. {timer} turns.")
            state["active_fuses"].append({"timer": timer})
            state["player_nerve"] -= 15
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

    state["player_nerve"] = clamp(state["player_nerve"], 0, state["max_nerve"])
    return False


# ------------------ DEALER AI ------------------

def dealer_turn(state):
    print("\nDEALER TURN")

    # Dealer fuse handling
    if state["dealer_fuse"] is not None:
        state["dealer_fuse"] -= 1
        print("Dealer fuse ticking...")
        if state["dealer_fuse"] <= 0:
            print("Dealer explodes.")
            state["dealer_health"] -= 2
            state["dealer_fuse"] = None

    if not state["shell_list"]:
        return

    # Smart targeting logic
    shell = state["shell_list"][0]  # peek

    aggressive = state["difficulty"] >= 2

    if shell == "blank" and aggressive and state["dealer_health"] > state["player_health"]:
        target = "self"
    else:
        target = "player"

    shell = state["shell_list"].pop(0)

    if target == "self":
        print("Dealer shoots self.")
        if shell == "live":
            state["dealer_health"] -= 1
        elif "fuse" in shell:
            state["dealer_fuse"] = int(shell.split("_")[1])
        else:
            print("Blank.")
        return

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

    state["player_nerve"] = clamp(state["player_nerve"], 0, state["max_nerve"])


# ------------------ GAME LOOP ------------------

def play_game():
    print("Select Difficulty: 1 = Easy | 2 = Normal | 3 = Hard")
    difficulty = int(input("Choice: "))
    difficulty = clamp(difficulty, 1, 3)

    state = {
        "player_health": 4,
        "dealer_health": 4,
        "player_nerve": 75,
        "max_nerve": 100,
        "active_fuses": [],
        "dealer_fuse": None,
        "shell_list": [],
        "player_items": [],
        "difficulty": difficulty
    }

    for round_num in range(1, 4):
        print(f"\n=== ROUND {round_num} ===")
        give_items(state)
        state["shell_list"] = generate_shells(round_num, difficulty)

        while state["player_health"] > 0 and state["dealer_health"] > 0:
            if not state["shell_list"]:
                state["shell_list"] = generate_shells(round_num, difficulty)

            if player_turn(state):
                continue
            dealer_turn(state)

        if state["player_health"] <= 0:
            print("You died in Limbo.")
            return

        print("Dealer defeated.")
        state["dealer_health"] = 4 + round_num
        state["max_nerve"] -= 10
        state["player_nerve"] = clamp(state["player_nerve"], 0, state["max_nerve"])

    print("\nYou survived all rounds.")


while True:
    play_game()
    again = input("Play again? (Y/N): ").strip().upper()
    if again != "Y":
        break

import json

with open("fun/genesis5.json", "r", encoding="utf-8") as f:
    genealogy = json.load(f)

# Generic template
def standard_entry(name, son, age_son_born, age_after):
    total_age = age_son_born + age_after
    return (
        f"When {name} had lived {age_son_born} years, he became the father of {son}. "
        f"{name} lived {age_after} years after he became the father of {son}, and he had other sons and daughters. "
        f"The entire lifetime of {name} was {total_age} years, and then he died.\n"
    )

# Special templates
def adam_entry(p):
    total_age = p["age_son_born"] + p["age_after"]
    return (
        f"When Adam had lived {p['age_son_born']} years he fathered a son in his own likeness, "
        f"according to his image, and he named him {p['son_name']}. "
        f"The length of time Adam lived after he became the father of {p['son_name']} was {p['age_after']} years; "
        f"during this time he had other sons and daughters. "
        f"The entire lifetime of Adam was {total_age} years, and then he died.\n"
    )

def enoch_entry(p):
    total_age = p["age_son_born"] + p["age_after"]
    return (
        f"When Enoch had lived {p['age_son_born']} years, he became the father of {p['son_name']}. "
        f"After he became the father of {p['son_name']}, Enoch {p['notes']} for {p['age_after']} years, "
        f"and he had other sons and daughters. "
        f"The entire lifetime of Enoch was {total_age} years. "
        f"Enoch {p['notes']}, and then he disappeared because God took him away.\n"
    )

def lamech_entry(p):
    total_age = p["age_son_born"] + p["age_after"]
    return (
        f"When Lamech had lived {p['age_son_born']} years, he had a son. "
        f"He named him {p['son_name']}, saying, “{p['notes']}” "
        f"Lamech lived {p['age_after']} years after he became the father of {p['son_name']}, "
        f"and he had other sons and daughters. "
        f"The entire lifetime of Lamech was {total_age} years, and then he died.\n"
    )

def noah_entry(p):
    total_age = p["age_son_born"] + p["age_after"]
    return (
        f"After Noah was {p['age_son_born']} years old, he became the father of {p['son_name']}.\n"
        f"And Noah did all that the Lord commanded him.\n"
        f"Noah was 600 years old when the floodwaters engulfed the earth. "
        f"After the flood Noah lived {p['age_after']} years. "
        f"The entire lifetime of Noah was {total_age} years, and then he died.\n"
    )

# Print chapter
for p in genealogy:
    if p["name"] == "Adam":
        print(adam_entry(p))
    elif p["name"] == "Enoch":
        print(enoch_entry(p))
    elif p["name"] == "Lamech":
        print(lamech_entry(p))
    elif p["name"] == "Noah":
        print(noah_entry(p))
    else:
        print(standard_entry(p["name"], p["son_name"], p["age_son_born"], p["age_after"]))

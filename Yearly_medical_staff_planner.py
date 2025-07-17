from pulp import *
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict
import random
import matplotlib.pyplot as plt
# ========================
# 1. DÉFINITIONS DE BASE
# ========================

medecins = [
    "El Amrani Youssef", "Bencheikh Khadija", "Bouzid Omar", "El Fassi Salma", 
    "Aït Taleb Rachid", "Harrak Nisrine", "Bensouda Anas", 
    "Zahra El Idrissi Fatima", "Touimi Hicham"
]
creneaux = ["AM", "PM", "GA"]
annee = 2025
jours = [date(annee, 1, 1) + timedelta(days=i) for i in range(365)]
jours_sem = [j for j in jours if j.weekday() < 5]  
# Spécialités par activité
specialites = {
    "Pédiatrie": ["El Amrani Youssef", "Bencheikh Khadija", "Bouzid Omar"],
    "Urgences": ["Bouzid Omar", "El Fassi Salma", "Bensouda Anas"],
    "Consultations": ["Aït Taleb Rachid", "Bensouda Anas"],
    "Exploration": ["Harrak Nisrine", "Zahra El Idrissi Fatima"],
    "Astreinte": ["Zahra El Idrissi Fatima", "Bensouda Anas"],
    "Maternité": ["Zahra El Idrissi Fatima", "Touimi Hicham", "Aït Taleb Rachid"],
    "Néonatologie": ["Zahra El Idrissi Fatima", "Touimi Hicham", "El Fassi Salma"]
}
activites = list(specialites.keys())

# ========================
# 2. BESOINS
# ========================
besoins = {}
for j in jours_sem:
    besoins[(j, "AM", "Pédiatrie")] = 2
    besoins[(j, "PM", "Pédiatrie")] = 1
    besoins[(j, "PM", "Consultations")] = 1
    besoins[(j, "AM", "Maternité")] = 1
for j in jours:
    besoins[(j, "AM", "Urgences")] = 1
    besoins[(j, "PM", "Urgences")] = 1
    besoins[(j, "GA", "Astreinte")] = 1
    besoins[(j, "AM", "Néonatologie")] = 1
    besoins[(j, "PM", "Néonatologie")] = 1
    besoins[(j, "GA", "Néonatologie")] = 1
    if j.weekday() == 2:
        besoins[(j, "AM", "Exploration")] = 1


# ========================
# 3. MODÉLISATION
# ========================

# Générer une disponibilité aléatoire par médecin, respectant 60 jours de repos max
repos_max = 60
disponibilites = {}
for med in medecins:
    jours_repos = set(random.sample(jours, repos_max))
    for j in jours:
        dispo = 0 if j in jours_repos else 1
        disponibilites[(med, j)] = dispo  # dictionnaire clé = (médecin, jour)
        

# Priorités des activités 
priorites = {
    "Urgences": 0.1,
    "Pédiatrie": 0.1,
    "Astreinte": 0.1,
    "Maternité": 0.1,
    "Néonatologie": 0.1,
    "Consultations": 0.5,
    "Exploration": 0.5
}

# Création du modèle
model = LpProblem("Planning_Medecins", LpMinimize)

# Variables
x = LpVariable.dicts("x", (medecins, jours, creneaux, activites), cat="Binary")
y = LpVariable.dicts("y", besoins.keys(), lowBound=0, cat="Integer")
delta = LpVariable.dicts("delta", medecins, lowBound=0)

alpha,  gamma = 1,  1
Z1 = lpSum([y[(j, t, a)] for j in jours for t in creneaux for a in activites if (j, t, a) in y])
Z3 = lpSum([(1 - priorites[a]) * x[m][j][t][a]
            for m in medecins for j in jours for t in creneaux for a in activites])
model += alpha * Z1  + gamma * Z3


# 1. Couverture des besoins
for (j, c, a), required in besoins.items():
    model += lpSum(
        x[m][j][c][a]
        for m in medecins
        if m in specialites.get(a, []) and disponibilites.get((m, j), 0) == 1
    ) + y[(j, c, a)] == required, f"Besoin_{j}{c}{a}"


# 3. Limite de créneaux par semaine (max = 10)
for m in medecins:
    for week in range(0, 30, 7):
        semaine = jours[week:week + 7]
        model += lpSum(x[m][j][c][a] for j in semaine for c in ["AM", "PM","GA"] for a in activites) <=10

# 4. Repos après garde de nuit
for m in medecins:
    for i in range(len(jours) - 1):
        j_nuit = jours[i]
        j_suiv = jours[i + 1]
        model += lpSum(x[m][j_suiv][c][a] for c in ["AM", "PM"] for a in activites) <= \
                 2*(1 - lpSum(x[m][j_nuit]["GA"][a] for a in activites)), f"Repos_{m}_{j_nuit}"

# 5. Équilibrage des charges
charge_totale = lpSum([x[m][j][t][a] for m in medecins for j in jours for t in creneaux for a in activites])
moyenne = charge_totale / len(medecins)
for m in medecins:
    model += lpSum(x[m][j][c][a] for j in jours for c in creneaux for a in activites) - moyenne <= delta[m]
    model += moyenne - lpSum(x[m][j][c][a] for j in jours for c in creneaux for a in activites) <= delta[m]
# Résolution du modèle
model.solve()

# Affichage du statut de la solution
print("Statut de la solution :", LpStatus[model.status])

#Afficher les manques de médecins (remplaçants requis)
print("\n--- Affectations des médecins ---")
# Dictionnaire pour stocker les affectations par semaine
affectations_par_semaine = defaultdict(lambda: defaultdict(int))
semaines = [jours[i:i + 7] for i in range(0, len(jours), 7)]
# Parcourir toutes les affectations
for m in medecins:
    for j in jours:
        for c in creneaux:
            for a in activites:
                if x[m][j][c][a].varValue == 1:
                    # Trouver à quelle semaine appartient le jour j
                    for i, semaine in enumerate(semaines):
                        if j in semaine:
                            affectations_par_semaine[m][i + 1] += 1  # semaine 1-indexée
                            break

# Affichage
print("\n📅 Nombre d'affectations par semaine pour chaque médecin :\n")
for m in medecins:
    print(f"🧑‍⚕️ {m}")
    for s in sorted(affectations_par_semaine[m].keys()):
        print(f"  - Semaine {s} : {affectations_par_semaine[m][s]} affectations")
    print()

# Afficher les besoins non couverts 
import pandas as pd
# Export CSV
affectations = []
for m in medecins:
    for j in jours:
        for c in creneaux:
            for a in activites:
                if x[m][j][c][a].varValue == 1:
                    affectations.append({"Médecin": m, "Jour": j.strftime('%Y-%m-%d'), "Créneau": c, "Activité": a})

df_affectations = pd.DataFrame(affectations)

# Ajouter une colonne "JourCréneau"
df_affectations["JourCréneau"] = df_affectations["Jour"].astype(str) + "_" + df_affectations["Créneau"]

# Créer un tableau pivot : lignes = Activités, colonnes = JourCréneau, valeurs = Médecins
pivot = df_affectations.groupby(["Activité", "JourCréneau"])["Médecin"] \
    .apply(lambda x: ", ".join(x)).unstack().fillna("")

# Exporter vers fichier CSV
pivot.to_csv("affectations_year.csv")
print("\n✅ Fichier 'affectations.csv' généré avec succès !")

# Export remplaçants
remplacants = [
    {"Jour": j.strftime('%Y-%m-%d'), "Créneau": c, "Activité": a, "Remplaçants": int(y[(j, c, a)].varValue)}
    for (j, c, a) in besoins if y[(j, c, a)].varValue > 0
]

df_remplacants = pd.DataFrame(remplacants)
df_remplacants["JourCréneau"] = df_remplacants["Jour"] + "_" + df_remplacants["Créneau"]
pivot_rempl = df_remplacants.pivot_table(index="Activité", columns="JourCréneau", values="Remplaçants", aggfunc="sum").fillna(0)
pivot_rempl.to_csv("remplacants_year.csv")


# Calcul de la charge de chaque médecin
charges = {
    m: sum(x[m][j][c][a].varValue for j in jours for c in creneaux for a in activites)
    for m in medecins
}

# Moyenne
charge_moyenne = sum(charges.values()) / len(medecins)

# Tracer
plt.figure(figsize=(10, 6))
plt.bar(charges.keys(), charges.values(), color="skyblue", label="Charge médecin")
plt.axhline(charge_moyenne, color='red', linestyle='--', label=f'Moyenne ({charge_moyenne:.1f})')

plt.xticks(rotation=45, ha='right')
plt.ylabel("Nombre d'affectations")
plt.title("Charge de travail par médecin pendant l'année 2025")
plt.legend()
plt.tight_layout()
plt.grid(axis='y', linestyle=':', alpha=0.7)

plt.savefig("charges_medecins.png")
plt.show()



from pulp import *
import pandas as pd
import matplotlib.pyplot as plt

# ========================
# 1. DÉFINITIONS DE BASE
# ========================

medecins = [
    "El Amrani Youssef", "Bencheikh Khadija", "Bouzid Omar", "El Fassi Salma", 
    "Aït Taleb Rachid", "Harrak Nisrine", "Bensouda Anas", 
    "Zahra El Idrissi Fatima", "Touimi Hicham"
]

jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
creneaux = ["AM", "PM", "GA"]
jours_sem = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

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
    
besoins[("Mercredi", "AM", "Exploration")] = 1

# ========================
# 3. MODÉLISATION
# ========================
# Disponibilités (initialisées à 1 sauf pour un médecin)
disponibilites = {}
for m in medecins:
    for (j, c, a), required in besoins.items():
                disponibilites[(m, j, c, a)] = 0  if m == "Bensouda Anas" else 1


# Priorités des activités (plus petite = plus prioritaire)
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

alpha, gamma = 1,1
Z1 = lpSum([y[k] for k in y])
Z3 = lpSum([(1 - priorites[a]) * x[m][j][t][a]
            for m in medecins for j in jours for t in creneaux for a in activites])
model += alpha * Z1 + gamma * Z3


# 1. Couverture des besoins
for (j, c, a), required in besoins.items():
    model += lpSum(
        x[m][j][c][a]
        for m in medecins
        if m in specialites.get(a, []) and disponibilites.get((m, j, c, a), 0) == 1
    ) + y[(j, c, a)] == required, f"Besoin_{j}{c}{a}"


# 2. Limite de créneaux par semaine (max = 10)
for m in medecins:
    model += lpSum(x[m][j][c][a] for j in jours for c in ["AM", "PM","GA"] for a in activites) <= 10, f"MaxHebdo_{m}"

# 3. Repos après garde de nuit
for m in medecins:
    for i in range(len(jours) - 1):
        j_nuit = jours[i]
        j_suiv = jours[i + 1]
        model += lpSum(x[m][j_suiv][c][a] for c in ["AM", "PM"] for a in activites) <= \
                2*( 1 - lpSum(x[m][j_nuit]["GA"][a] for a in activites)), f"Repos_{m}_{j_nuit}"

# 4. Équilibrage des charges
charge_totale = lpSum([x[m][j][t][a] for m in medecins for j in jours for t in creneaux for a in activites])
moyenne = charge_totale / len(medecins)
for m in medecins:
    model += lpSum(x[m][j][c][a] for j in jours for c in creneaux for a in activites) - moyenne <= delta[m]
    model += moyenne - lpSum(x[m][j][c][a] for j in jours for c in creneaux for a in activites) <= delta[m]

# 5.Un médecin ne peut être affecté à plus d'une activité dans le même créneau d’un jour donné
for m in medecins:
    for j in jours:
        for c in creneaux:
            model += lpSum(x[m][j][c][a] for a in activites) <= 1, f"UniqueActivite_{m}_{j}_{c}"


# Résolution du modèle
model.solve()

# Affichage du statut de la solution
print("Statut de la solution :", LpStatus[model.status])

#Afficher les manques de médecins (remplaçants requis)
print("\n--- Affectations des médecins ---")
for m in medecins:
    for (j, c, a), required in besoins.items():
                if x[m][j][c][a].varValue == 1:
                    print(f"{m} affecté à {a} ({c}) le {j}")


# Affectations
affectations = []
for m in medecins:
    for j in jours:
        for c in creneaux:
            for a in activites:
                if x[m][j][c][a].varValue == 1:
                    affectations.append({"Médecin": m, "Jour": j, "Créneau": c, "Activité": a})

df_affectations = pd.DataFrame(affectations)
ordre_colonnes = [f"{j}_{c}" for j in jours for c in creneaux]

# Trier par jour/créneau/activité
df_affectations["Jour"] = pd.Categorical(df_affectations["Jour"], categories=jours, ordered=True)
df_affectations = df_affectations.sort_values(by=["Jour", "Créneau", "Activité"])

# Créer le pivot
df_affectations["JourCréneau"] = df_affectations["Jour"].astype(str) + "_" + df_affectations["Créneau"]
pivot = df_affectations.groupby(["Activité", "JourCréneau"])["Médecin"] \
    .apply(lambda x: ", ".join(x)).unstack().fillna("")

# Réorganiser les colonnes
pivot = pivot.reindex(columns=ordre_colonnes, fill_value="")
pivot.to_csv("affectations_week.csv")
# Remplaçants
remplacants = []
for (j, c, a), required in besoins.items():
    if y[(j, c, a)].varValue > 0:
        remplacants.append({"Jour": j, "Créneau": c, "Activité": a, "Remplaçants": int(y[(j, c, a)].varValue)})

df_remplacants = pd.DataFrame(remplacants)
df_remplacants.to_csv("remplacants_week.csv", index=False)

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
plt.title("Charge de travail par médecin pendant une semaine")
plt.legend()
plt.tight_layout()
plt.grid(axis='y', linestyle=':', alpha=0.7)

plt.savefig("charges_medecins.png")
plt.show()
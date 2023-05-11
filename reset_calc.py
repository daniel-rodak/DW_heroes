import service as gs
import pandas as pd
import seaborn as sns
import numpy as np
from scipy.stats import gaussian_kde
from scipy.integrate import quad
from scipy.optimize import root_scalar
import matplotlib.pyplot as plt
from IPython.display import display

# Include when executing in a notebook
# %matplotlib inline

NAME_COL = 'Nick'
SSID = "1SBqYJBRLzkLk7Z7j5V7pq_U6Mbe2VDPZQAZJj7_hbzo"
STAMINA = 1100
N_TRIES = 2000


def lhside(a, kde, r):
    first_term = quad(lambda x: x*kde(x), a, np.inf)[0]
    second_term = a * (quad(kde, 0, a)[0] - 1/(1-r))
    return first_term + second_term


def fight(dmgs, probs):
    return np.random.choice(dmgs, 1, p=probs/(np.sum(probs)))[0]


def get_reset_point(dfl):
    kde = gaussian_kde(dfl['Dmg'])
    # sol = root_scalar(lambda x: lhside(x, kde, 1/12), bracket=(0, dfl['Dmg'].max()))
    sol = root_scalar(lambda x: lhside(x, kde, 1/12), x0=dfl['Dmg'].mean(), x1=dfl['Dmg'].median())
    return kde, sol


def get_report(values):
    df = pd.DataFrame(values[1:], columns=values[0])
    dfl = df.melt(NAME_COL, value_name="Dmg").drop(columns="variable").dropna()
    dfl[NAME_COL] = dfl[NAME_COL].str.strip()
    dfl['Dmg'] = dfl['Dmg'].astype(float)
    dmg_frame = (
        dfl
        .groupby(NAME_COL)
        .agg({'Dmg': ['mean', 'std', 'count']})
        .assign(Has_enough_data = lambda df: df[('Dmg', 'count')] >= 50)
    )
    display(dmg_frame)

    # sns.kdeplot(x='Dmg', hue=NAME_COL, data=dfl)

    ## Plot

    _, ax = plt.subplots(figsize=(6,6))
    sns.violinplot(x='Dmg', y=NAME_COL, data=dfl, ax=ax)
    plt.show()
    
    res = []
    for player in dfl[NAME_COL].unique():
        kde, sol = get_reset_point(dfl[dfl[NAME_COL]==player])
        res.append((player, np.round(sol.root)))

    reset_point_frame = pd.DataFrame(res, columns=[NAME_COL, 'Reset'])
    display(reset_point_frame)

    ## One reset

    kde, sol = get_reset_point(dfl)
    print(f"Other players reset below: {sol.root:.0f}M")

    return kde, sol, dfl, dmg_frame, reset_point_frame



def main():

    service = gs.connect()
    sheet = service.spreadsheets()

    ranges = {
        "Baelinda!A1:K1000": "Baelinda",
        "Rem!A1:K1000": "Rem",
        "ABaden_C!A1:K1000": "ABaden_C",
        "ABrutus_D!A1:K1000": "ABrutus_D",
        "Drez_Silas!A1:K1000": "Drez_Silas",
        "Wathalia_Skreg!A1:K1000": "Wathalia_Skreg",
    }

    for r, s in ranges.items():
        print(f"##### Team: {s} #####")
        result = sheet.values().get(spreadsheetId=SSID, range=r).execute()
        values = result.get('values', [])
        kde, sol, dfl, dmg_frame, reset_point_frame = get_report(values)

    ## Simulate 

        dmgs = np.linspace(1,15000,15000)
        probs = kde(dmgs)

        ### No reset
        no_reset = quad(lambda x: x*kde(x), 0, np.inf)[0]
        no_reset_dmgs = []
        for i in range(N_TRIES):
            stamina = STAMINA
            attacks = []
            while stamina>48:
                d = fight(dmgs, probs)
                attacks.append(d)
                stamina = stamina - 48
            tot_dmg = np.sum(attacks)
            no_reset_dmgs.append(tot_dmg)


        ### Reset
        reset_dmgs = []
        stamina = STAMINA
        ref_dmg = (stamina // 48) * no_reset
        for i in range(N_TRIES):
            stamina = STAMINA
            attacks = []
            while stamina>48:
                d = fight(dmgs, probs)
                if d < sol.root:
                    stamina = stamina - 4
                else:
                    attacks.append(d)
                    stamina = stamina - 48
            mean_dmg = np.mean(attacks)
            tot_dmg = np.sum(attacks)
            n_attacks = len(attacks)
            reset_dmgs.append(tot_dmg)

        gain = (np.average(reset_dmgs) - np.average(no_reset_dmgs)) / (STAMINA // 48)
        pct_gain = gain/(np.average(no_reset_dmgs) / (STAMINA // 48))
        print(f"Gain from the reset strategy: {gain:.0f}M ({pct_gain*100:.0f}%) per 48 stamina")

        write_frame = dmg_frame.merge(reset_point_frame, on='Nick')
        write_frame.columns = [NAME_COL, 'Mean Damage', 'Damage deviation', 'Tests count', 'Has enough data', 'Reset point']
        write_frame = write_frame.loc[:,[NAME_COL, 'Reset point', 'Mean Damage', 'Damage deviation', 'Has enough data', 'Tests count']]
        gs.update_values(SSID, f"{s}!M2:R{len(write_frame)+2}", "RAW", write_frame.to_numpy().tolist())


if __name__ == '__main__':
    main()

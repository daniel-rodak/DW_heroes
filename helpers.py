import numpy as np
import pandas as pd

asc_dict = {'-': 16, 'E': 15, 'E+': 14, 'L': 12, 'L+': 10, 'M': 8, 'M+': 6, 'A': 0}

class Hero():
    def __init__(self, name:str, min_desc: str, opt_desc: str, whl_desc: str = None, priority: int = None):
        self.name = name
        self.min = self.get_hero_stats(min_desc)
        self.opt = self.get_hero_stats(opt_desc)
        self.whl = self.get_hero_stats(whl_desc)
        self.sig = pd.read_csv('sig.csv')
        self.engr = pd.read_csv('engr.csv')
        self.priority = priority
    
    def get_hero_stats(self, desc):
        desc_split = desc.split(' ')
        if len(desc_split) > 0 and len(desc_split) < 4:
            desc_split = desc_split + [0 for r in range(4 - len(desc_split))]
        desc_split[1:] = [int(d) for d in desc_split[1:]]
        return desc_split

    def asc_gte(self, A1, A2):
        asc_list = np.array(['-', 'E', 'E+', 'L', 'L+', 'M', 'M+', 'A'])
        return np.where(asc_list==A1)[0][0] >= np.where(asc_list==A2)[0][0]

    def hero_satisfies(self, stats, ref_stats):
        c1 = self.asc_gte(stats[0], ref_stats[0])
        c2 = stats[1] >= ref_stats[1]
        c3 = stats[2] >= ref_stats[2]
        c4 = stats[3] >= ref_stats[3]
        return c1 and c2 and c3 and c4

    def get_status(self, desc: str):
        try:
            stats = self.get_hero_stats(desc)
            if self.hero_satisfies(stats, self.whl):
                return 'Whale'
            elif self.hero_satisfies(stats, self.opt):
                return 'Optimum'
            elif self.hero_satisfies(stats, self.min):
                return 'Minimum'
            else:
                return 'Dupa'
        except Exception as e:
            print(f"For hero {self.name} error occurred: {e}")
            return 'Dupa'
    
    def compute_resources(self, desc, target):
        if target=='Minimum':
            target_stats = self.min
        if target=='Optimum':
            target_stats = self.opt
        if target=='Whale':
            target_stats = self.whl
        try:
            stats = self.get_hero_stats(desc)
        except Exception as e:
            print(f"For hero {self.name} error occurred: {e}")
            stats = self.get_hero_stats("-")
        
        # Signature item
        sig_to_make = self.sig.loc[(self.sig.Level > stats[1]) & (self.sig.Level <= target_stats[1]), :]
        sig_cost = sig_to_make.loc[:,['si_silver', 'si_gold', 'si_red']].sum().astype('int')

        # Furniture
        furn_cost = pd.Series({'meble': np.max([target_stats[2] - stats[2], 0])})

        # Engraving
        engr_to_make = self.engr.loc[(self.engr.Level > stats[3]) & (self.engr.Level <= target_stats[3]), :]
        engr_cost = engr_to_make.loc[:,['engr_yellow', 'engr_red']].sum().astype('int')

        return pd.concat([sig_cost, furn_cost, engr_cost])
    
    def __str__(self):
        return self.name


def get_costs(dw_descs, heroes, cost_type = 'Optimum'):
    costs = []
    for row in dw_descs.iterrows():
        df = []
        for hero in heroes.keys():
            x = heroes[hero].compute_resources(row[1][hero].strip(), cost_type)
            x = pd.concat([pd.Series({'Nick': row[0], 'Priorytet': heroes[hero].priority}), x])
            df.append(x)
        cost = pd.DataFrame(df)
        # cost['equiv'] = cost['meble']*9000/5000 + cost['si_red']/25 + cost['engr_red']/167 + cost['engr_yellow']/333
        cost = cost.groupby(['Nick', 'Priorytet']).sum().reset_index()
        costs.append(cost)
    return pd.concat(costs)

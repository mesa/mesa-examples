import mesa
import geopandas as gpd
import pandas as pd
import numpy as np
import os
from agents import MSOAAgent, CommuterAgent


class LondonCommuteModel(mesa.Model):
    """
    Agent-Based Model of daily commuting in London.
    Each step = one hour (0am-11pm, 24 steps per day).
    Commuters have fixed workplaces from real OD flow probabilities.
    Travel time computed via BPR function using straight-line distance
    with circuity factor as free-flow time proxy.
    Congestion ratios from TomTom data (Borough level, hourly).
    Accessibility = Σ E_j * exp(-beta * BPR_travel_time).
    """

    def __init__(self, n_commuters=5000, bpr_beta=3.0, alpha=1.0, seed=None):
        super().__init__(seed=seed)

        self.n_commuters = n_commuters
        self.alpha = alpha
        self.current_hour = 0
        self.beta_acc = 1.0

        # BPR parameters
        self.bpr_alpha = 0.15
        self.bpr_beta = bpr_beta
        self.circuity_factor = 1.3
        self.avg_speed_kmh = 20.0

        # Hourly flow multiplier (relative traffic volume, peak=1.0)
        # index 0=0am, 1=1am, ..., 23=11pm
        # Used to scale car flow in BPR — derived from typical London traffic patterns
        self.hourly_flow_multiplier = [
            0.05,  # 0am - 深夜
            0.03,  # 1am
            0.02,  # 2am
            0.02,  # 3am
            0.05,  # 4am
            0.15,  # 5am
            0.35,  # 6am
            0.65,  # 7am
            1.00,  # 8am  ← morning peak (baseline)
            0.90,  # 9am
            0.70,  # 10am
            0.60,  # 11am
            0.60,  # 12pm
            0.60,  # 1pm
            0.65,  # 2pm
            0.70,  # 3pm
            0.80,  # 4pm
            0.95,  # 5pm  ← evening peak
            0.85,  # 6pm
            0.60,  # 7pm
            0.40,  # 8pm
            0.25,  # 9pm
            0.15,  # 10pm
            0.08,  # 11pm
        ]

        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, 'data', 'processed')

        self.od_df = pd.read_csv(os.path.join(data_dir, 'london_OD_travel2work.csv'))
        self.gdf = gpd.read_file(os.path.join(data_dir, 'london_msoa_boundaries.geojson'))

        # Employment attraction: total inflow per MSOA
        emp = self.od_df.groupby('MSOA21CD_work')['count'].sum()
        self.employment_attraction = emp.to_dict()

        # OD candidates and weights per home MSOA
        self.work_candidates = {}
        self.work_weights = {}
        for home, group in self.od_df.groupby('MSOA21CD_home'):
            self.work_candidates[home] = group['MSOA21CD_work'].tolist()
            weights = group['count'].values.astype(float)
            self.work_weights[home] = (weights / weights.sum()).tolist()

        # OD capacity = observed flow (vectorised — avoid slow iterrows)
        _cap = self.od_df[['MSOA21CD_home', 'MSOA21CD_work', 'count']].copy()
        _cap['count'] = _cap['count'].clip(lower=1)
        self.od_capacity = dict(zip(
            zip(_cap['MSOA21CD_home'], _cap['MSOA21CD_work']),
            _cap['count']
        ))

        # Create MSOA Agents
        self.msoa_agents = {}
        msoa_agents_list = [MSOAAgent(model=self) for _ in range(len(self.gdf))]

        for agent, (_, row) in zip(msoa_agents_list, self.gdf.iterrows()):
            agent.msoa_code = row['MSOA21CD']
            agent.msoa_name = row['MSOA21NM']
            agent.lat = row['LAT']
            agent.lon = row['LONG']
            agent.employment_attraction = self.employment_attraction.get(
                row['MSOA21CD'], 0
            )
            self.msoa_agents[row['MSOA21CD']] = agent

        # Pre-compute free-flow travel time for all observed OD pairs (vectorised)
        _coords = self.gdf.set_index('MSOA21CD')[['LAT', 'LONG']]
        _od = self.od_df[['MSOA21CD_home', 'MSOA21CD_work']].copy()
        _od = _od.merge(_coords.rename(columns={'LAT': 'h_lat', 'LONG': 'h_lon'}),
                        left_on='MSOA21CD_home', right_index=True, how='inner')
        _od = _od.merge(_coords.rename(columns={'LAT': 'w_lat', 'LONG': 'w_lon'}),
                        left_on='MSOA21CD_work', right_index=True, how='inner')
        _od = _od.reset_index(drop=True)
        _dist_deg = np.sqrt((_od['h_lat'] - _od['w_lat'])**2 +
                            (_od['h_lon'] - _od['w_lon'])**2)
        _t0 = np.maximum(0.5 / 60,
                         _dist_deg * 111 * self.circuity_factor / self.avg_speed_kmh)
        _mask = _t0 <= 2.0
        self.free_flow_time = dict(zip(
            zip(_od.loc[_mask, 'MSOA21CD_home'], _od.loc[_mask, 'MSOA21CD_work']),
            _t0[_mask]
        ))

        # Load TomTom hourly congestion ratios per MSOA (vectorised)
        congestion_path = os.path.join(data_dir, 'msoa_hourly_congestion.csv')
        congestion_df = pd.read_csv(congestion_path)
        hour_cols = [f'hour_{h}' for h in range(24)]
        self.msoa_congestion = {
            row['MSOA21CD']: {h: row[f'hour_{h}'] for h in range(24)}
            for row in congestion_df[['MSOA21CD'] + hour_cols].to_dict('records')
        }

        # Load commute mode proportions
        mode_path = os.path.join(data_dir, 'london_commute_mode_msoa.csv')
        mode_df = pd.read_csv(mode_path)
        self.commute_mode_props = mode_df.set_index('MSOA11CD')[
            ['prop_car', 'prop_pt', 'prop_active']
        ].to_dict('index')

        # Load occupation proportions per home MSOA
        occ_path = os.path.join(data_dir, 'london_occupation_msoa.csv')
        occ_df = pd.read_csv(occ_path)
        self.occupation_props = occ_df.set_index('MSOA21CD')[
            [f'prop_soc{i}' for i in range(1, 10)]
        ].to_dict('index')

        # Load SOC work attraction weights
        import json
        with open(os.path.join(data_dir, 'soc_work_attraction.json'), 'r') as f:
            self.soc_work_attraction = json.load(f)

        # Load BRES industry employment per work MSOA
        bres_path = os.path.join(data_dir, 'london_bres_msoa.csv')
        bres_df = pd.read_csv(bres_path)
        self.work_msoa_employment = bres_df.set_index('MSOA21CD')['total_employment'].to_dict()
        
        # Real accessibility: gravity model with exponential decay (vectorised)
        _ff_df = pd.DataFrame(
            [(h, w, t) for (h, w), t in self.free_flow_time.items()],
            columns=['home', 'work', 't0']
        )
        _ff_df['emp_attr'] = _ff_df['work'].map(self.employment_attraction).fillna(0)
        _ff_df['acc'] = _ff_df['emp_attr'] * np.exp(-self.beta_acc * _ff_df['t0'])
        self.real_accessibility = _ff_df.groupby('home')['acc'].sum().to_dict()

        # Create Commuter Agents
        home_counts = self.od_df.groupby('MSOA21CD_home')['count'].sum()
        home_msoas = home_counts.index.tolist()
        weights = home_counts.values / home_counts.values.sum()
        sampled_homes = self.rng.choice(home_msoas, size=n_commuters, p=weights)

        commuter_list = []
        for home_code in sampled_homes:
            commuter = CommuterAgent(model=self)
            commuter.home_msoa = home_code

            # Assign occupation based on home MSOA proportions
            if home_code in self.occupation_props:
                props = self.occupation_props[home_code]
                soc_keys = [f'prop_soc{i}' for i in range(1, 10)]
                soc_names = [f'soc{i}' for i in range(1, 10)]
                soc_weights = [props.get(k, 0) for k in soc_keys]
                commuter.occupation = self.random.choices(
                    soc_names, weights=soc_weights, k=1
                )[0]
            else:
                commuter.occupation = self.random.choices(
                    [f'soc{i}' for i in range(1, 10)],
                    weights=[0.11]*9, k=1
                )[0]

            # Assign commute mode
            if home_code in self.commute_mode_props:
                props = self.commute_mode_props[home_code]
                modes = ['car', 'pt', 'active']
                mode_weights = [props['prop_car'], props['prop_pt'], props['prop_active']]
            else:
                modes = ['car', 'pt', 'active']
                mode_weights = [0.341, 0.519, 0.132]
            commuter.commute_mode = self.random.choices(modes, weights=mode_weights, k=1)[0]

            # Assign workplace based on occupation-specific industry attraction
            # Blend OD-based weights with SOC-based attraction
            candidates = self.work_candidates.get(home_code, [])
            if candidates:
                od_weights = np.array(self.work_weights.get(home_code, []))

                # SOC-based attraction weights for these candidates
                soc_attraction = self.soc_work_attraction.get(commuter.occupation, {})
                soc_weights_arr = np.array([
                    soc_attraction.get(w, 1e-6) for w in candidates
                ])
                soc_weights_arr = soc_weights_arr / soc_weights_arr.sum()

                # Blend: 60% OD-based, 40% SOC-based
                blended = 0.6 * od_weights + 0.4 * soc_weights_arr
                blended = blended / blended.sum()

                commuter.chosen_work_msoa = self.random.choices(
                    candidates, weights=blended.tolist(), k=1
                )[0]

            commuter_list.append(commuter)

        self._msoa_agent_list = msoa_agents_list
        self._commuter_agent_list = commuter_list

        # Initialise accessibility at off-peak (hour=12)
        self._initialise_accessibility()

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Mean_Accessibility": self._mean_accessibility,
                "Accessibility_Gini": self._accessibility_gini,
                "Validation_Correlation": self._validation_correlation,
                "Hour": lambda m: m.current_hour,
                "Mean_Commute_Time": self._mean_commute_time,
                "Accessibility_Palma": self._accessibility_palma,
                "SOC1_Accessibility": lambda m: m._person_based_accessibility_by_occupation().get('soc1', 0),
                "SOC5_Accessibility": lambda m: m._person_based_accessibility_by_occupation().get('soc5', 0),
                "SOC9_Accessibility": lambda m: m._person_based_accessibility_by_occupation().get('soc9', 0),
                "SOC_Gap": lambda m: (
                    max(m._person_based_accessibility_by_occupation().values()) /
                    max(min(m._person_based_accessibility_by_occupation().values()), 1)
                ),
            },
            agent_reporters={
                "Accessibility": lambda a: (
                    a.accessibility if isinstance(a, MSOAAgent) else None
                ),
            }
        )
        self.datacollector.collect(self)

    def _person_based_accessibility_by_occupation(self):
        """Mean accessibility per SOC group."""
        soc_acc = {f'soc{i}': [] for i in range(1, 10)}
        msoa_acc = {a.msoa_code: a.accessibility for a in self._msoa_agent_list}
        for agent in self._commuter_agent_list:
            if agent.occupation and agent.home_msoa:
                acc = msoa_acc.get(agent.home_msoa, 0)
                soc_acc[agent.occupation].append(acc)
        return {
            soc: np.mean(vals) if vals else 0.0
            for soc, vals in soc_acc.items()
        }

    def _get_free_flow_time(self, home, work):
        return self.free_flow_time.get((home, work), 0.5)

    def _bpr_travel_time(self, home, work, flow, hour):
        t0 = self._get_free_flow_time(home, work)
        capacity = self.od_capacity.get((home, work), 1)
        congestion_ratio = self.msoa_congestion.get(work, {}).get(hour, 1.2)
        effective_capacity = capacity / congestion_ratio
        bpr_time = t0 * (1 + self.bpr_alpha * (flow / max(effective_capacity, 0.1)) ** self.bpr_beta)
        # Cap at 3x free-flow time to prevent extreme values
        return min(bpr_time, t0 * 3.0)

    def _mean_accessibility(self):
        values = [a.accessibility for a in self._msoa_agent_list if a.accessibility > 0]
        return np.mean(values) if values else 0.0

    def _accessibility_gini(self):
        values = sorted([a.accessibility for a in self._msoa_agent_list if a.accessibility > 0])
        if not values:
            return 0
        n = len(values)
        cumsum = np.cumsum(values)
        return (2 * sum((i + 1) * v for i, v in enumerate(values))
                / (n * cumsum[-1])) - (n + 1) / n

    def _accessibility_palma(self):
        values = sorted([a.accessibility for a in self._msoa_agent_list if a.accessibility > 0])
        if not values:
            return 0.0
        n = len(values)
        bottom_40 = values[:int(n * 0.4)]
        top_10 = values[int(n * 0.9):]
        if not bottom_40 or not top_10:
            return 0.0
        return np.mean(top_10) / np.mean(bottom_40)

    def _validation_correlation(self):
        sim_acc = {a.msoa_code: a.accessibility for a in self._msoa_agent_list}
        common = set(sim_acc.keys()) & set(self.real_accessibility.keys())
        if len(common) < 2:
            return 0.0
        sim_arr = np.array([sim_acc[k] for k in common])
        real_arr = np.array([self.real_accessibility[k] for k in common])
        if sim_arr.std() == 0 or real_arr.std() == 0:
            return 0.0
        return float(np.corrcoef(sim_arr, real_arr)[0, 1])

    def _mean_commute_time(self):
        times = [a.commute_time_minutes for a in self._commuter_agent_list
                 if a.commute_time_minutes > 0]
        return np.mean(times) if times else 0.0

    def _initialise_accessibility(self):
        """Initialise accessibility at off-peak (hour=12)."""
        init_hour = 12
        flow_multiplier = self.hourly_flow_multiplier[init_hour]

        od_flow = {}
        for agent in self._commuter_agent_list:
            if agent.chosen_work_msoa:
                key = (agent.home_msoa, agent.chosen_work_msoa)
                od_flow[key] = od_flow.get(key, 0) + 1

        scaled_flow = {k: v * flow_multiplier for k, v in od_flow.items()}
        travel_time = {
            key: self._bpr_travel_time(key[0], key[1], flow, init_hour)
            for key, flow in scaled_flow.items()
        }

        home_accessibility = {}
        for agent in self._commuter_agent_list:
            if agent.chosen_work_msoa:
                home = agent.home_msoa
                work_msoa = self.msoa_agents.get(agent.chosen_work_msoa)
                if work_msoa:
                    key = (home, agent.chosen_work_msoa)
                    if key not in self.free_flow_time:
                        continue
                    tt = travel_time.get(key, self.free_flow_time[key])
                    acc = work_msoa.employment_attraction * np.exp(-self.beta_acc * tt)
                    home_accessibility[home] = home_accessibility.get(home, 0) + acc

        for agent in self._msoa_agent_list:
            agent.accessibility = home_accessibility.get(agent.msoa_code, 0.0)

    def step(self):
        hour_idx = self.steps % 24
        self.current_hour = hour_idx
        flow_multiplier = self.hourly_flow_multiplier[hour_idx]

        # Split flows by commute mode
        od_flow_car = {}
        od_flow_pt = {}
        od_flow_active = {}

        for agent in self._commuter_agent_list:
            if agent.chosen_work_msoa:
                key = (agent.home_msoa, agent.chosen_work_msoa)
                if agent.commute_mode == 'car':
                    od_flow_car[key] = od_flow_car.get(key, 0) + 1
                elif agent.commute_mode == 'pt':
                    od_flow_pt[key] = od_flow_pt.get(key, 0) + 1
                else:
                    od_flow_active[key] = od_flow_active.get(key, 0) + 1

        # Car: BPR with TomTom congestion + flow multiplier
        scaled_flow_car = {k: v * flow_multiplier for k, v in od_flow_car.items()}
        travel_time_car = {
            key: self._bpr_travel_time(key[0], key[1], flow, self.current_hour)
            for key, flow in scaled_flow_car.items()
        }

        # PT: crowding penalty during peak based on TomTom congestion level
        london_avg_congestion = np.mean([
            self.msoa_congestion.get(key[1], {}).get(self.current_hour, 1.2)
            for key in od_flow_pt
        ]) if od_flow_pt else 1.2
        pt_multiplier = 1.1 if london_avg_congestion > 1.5 else 1.0
        travel_time_pt = {
            key: self._get_free_flow_time(key[0], key[1]) * pt_multiplier
            for key in od_flow_pt
        }

        # Active: always free flow
        travel_time_active = {
            key: self._get_free_flow_time(key[0], key[1])
            for key in od_flow_active
        }

        # Merge: active → pt → car
        travel_time = {}
        travel_time.update(travel_time_active)
        travel_time.update(travel_time_pt)
        travel_time.update(travel_time_car)

        # Compute accessibility and store commute time
        home_accessibility = {}
        for agent in self._commuter_agent_list:
            if agent.chosen_work_msoa:
                home = agent.home_msoa
                work_code = agent.chosen_work_msoa
                work_msoa = self.msoa_agents.get(work_code)
                if work_msoa:
                    key = (home, work_code)
                    if key not in self.free_flow_time:
                        continue
                    tt = travel_time.get(key, self.free_flow_time[key])
                    agent.commute_time_minutes = tt * 60
                    acc = work_msoa.employment_attraction * np.exp(-self.beta_acc * tt)
                    home_accessibility[home] = home_accessibility.get(home, 0) + acc

        # Update MSOA accessibility
        for agent in self._msoa_agent_list:
            agent.accessibility = home_accessibility.get(agent.msoa_code, 0.0)

        self.datacollector.collect(self)
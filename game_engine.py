import random
from typing import Dict, List, Tuple, Optional, Any

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
ROWS: int = 6
COLS: int = 6
MAX_WIN_CAP: float = 20000.0  # Multiplier cap (20,000x)
WILD_SYMBOL: str = 'W'
SYMBOLS: List[str] = ['💎', '🔮', '⚡', '🗝️', '🧬']

# Exact Paytable Multipliers (Base Bet Multipliers based on cluster sizes)
EXACT_PAYTABLE: Dict[str, Dict[int, float]] = {
    '💎': {5: 0.2, 8: 0.8, 12: 2.5, 15: 10.0, 20: 25.0},
    '🔮': {5: 0.2, 8: 0.8, 12: 2.5, 15: 10.0, 20: 25.0},
    '⚡': {5: 0.5, 8: 2.0, 12: 8.0, 15: 25.0, 20: 100.0},
    '🗝️': {5: 0.5, 8: 2.0, 12: 8.0, 15: 25.0, 20: 100.0},
    '🧬': {5: 1.0, 8: 5.0, 12: 20.0, 15: 100.0, 20: 500.0}
}

BET_LEVELS: List[float] = [1.00, 2.00, 5.00, 10.00, 20.00, 50.00, 100.00]


class WildHavocGameEngine:
    """
    Python backend game engine matching wild_havoc_3.html specifications.
    Handles grid generation, cluster evaluations, cascades, wild multipliers,
    meter charge mechanics, and bonus features.
    """

    def __init__(self, initial_balance: float = 10000.0, bet_index: int = 3):
        self.balance: float = initial_balance
        self.current_bet_index: int = bet_index
        self.base_bet: float = BET_LEVELS[self.current_bet_index]
        self.meter_points: int = 0
        self.bonus_level: int = 1
        
        self.grid_state: List[List[str]] = [["" for _ in range(COLS)] for _ in range(ROWS)]
        self.wild_multipliers: List[List[int]] = [[1 for _ in range(COLS)] for _ in range(ROWS)]
        self.mega_wild_region: Optional[Dict[str, Any]] = None
        
        self.init_grid()

    def set_bet_index(self, index: int) -> bool:
        if 0 <= index < len(BET_LEVELS):
            self.current_bet_index = index
            self.base_bet = BET_LEVELS[self.current_bet_index]
            return True
        return False

    def init_grid(self) -> None:
        """Initializes a new 6x6 grid with random symbols."""
        self.grid_state = []
        self.wild_multipliers = [[1 for _ in range(COLS)] for _ in range(ROWS)]
        self.mega_wild_region = None
        
        for r in range(ROWS):
            row = [random.choice(SYMBOLS) for _ in range(COLS)]
            self.grid_state.append(row)

    def get_random_symbol(self, is_low_win_prob: bool = False) -> str:
        """Weighted random symbol selection matching HTML JS logic."""
        if not is_low_win_prob:
            return random.choice(SYMBOLS)
        
        rand = random.random()
        if rand < 0.35:
            return SYMBOLS[0]  # 💎
        elif rand < 0.60:
            return SYMBOLS[1]  # 🔮
        elif rand < 0.80:
            return SYMBOLS[2]  # ⚡
        elif rand < 0.93:
            return SYMBOLS[3]  # 🗝️
        return SYMBOLS[4]      # 🧬

    def get_random_multiplier(self) -> int:
        """Generates a random multiplier tag for Wilds."""
        rand = random.random()
        if rand < 0.70:
            return random.randint(2, 5)
        return random.randint(6, 15)

    def spawn_mega_wild(self, size: int) -> None:
        """Spawns a Mega Wild box overlay on the grid."""
        start_r = random.randint(0, ROWS - size)
        start_c = random.randint(0, COLS - size)
        random_mult = self.get_random_multiplier()

        self.mega_wild_region = {
            'start_r': start_r,
            'start_c': start_c,
            'size': size,
            'multiplier': random_mult
        }

        for r in range(start_r, start_r + size):
            for c in range(start_c, start_c + size):
                self.grid_state[r][c] = WILD_SYMBOL
                self.wild_multipliers[r][c] = random_mult

    def calculate_cluster_win(self, symbol: str, cluster_size: int) -> float:
        """Calculates win amount for a given symbol and cluster count."""
        if cluster_size < 5:
            return 0.0
            
        tiers = EXACT_PAYTABLE.get(symbol)
        if not tiers:
            return self.base_bet * 0.2

        multiplier = 0.2
        if cluster_size >= 20:
            multiplier = tiers[20]
        elif cluster_size >= 15:
            multiplier = tiers[15]
        elif cluster_size >= 12:
            multiplier = tiers[12]
        elif cluster_size >= 8:
            multiplier = tiers[8]
        elif cluster_size >= 5:
            multiplier = tiers[5]

        return self.base_bet * multiplier

    def find_clusters(self) -> List[Dict[str, Any]]:
        """Identifies connected symbol clusters (matching standard or Wild rules)."""
        visited = [[False for _ in range(COLS)] for _ in range(ROWS)]
        detected_clusters = []

        for r in range(ROWS):
            for c in range(COLS):
                if visited[r][c] or self.grid_state[r][c] == '':
                    continue

                target_symbol = self.grid_state[r][c]
                current_cluster = []
                queue = [(r, c)]
                visited[r][c] = True
                primary_symbol = target_symbol

                while queue:
                    curr_r, curr_c = queue.pop(0)
                    current_cluster.append((curr_r, curr_c))

                    if primary_symbol == WILD_SYMBOL and self.grid_state[curr_r][curr_c] != WILD_SYMBOL:
                        primary_symbol = self.grid_state[curr_r][curr_c]

                    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for dr, dc in dirs:
                        new_r, new_c = curr_r + dr, curr_c + dc
                        if 0 <= new_r < ROWS and 0 <= new_c < COLS and not visited[new_r][new_c]:
                            sym = self.grid_state[new_r][new_c]
                            if sym == primary_symbol or sym == WILD_SYMBOL or primary_symbol == WILD_SYMBOL:
                                visited[new_r][new_c] = True
                                queue.append((new_r, new_c))

                if len(current_cluster) >= 5:
                    final_sym = '🧬' if primary_symbol == WILD_SYMBOL else primary_symbol
                    detected_clusters.append({
                        'symbol': final_sym,
                        'coords': current_cluster
                    })

        return detected_clusters

    def process_cascades(self, is_bonus_mode: bool = False, active_feature_mode: Optional[str] = None, max_win_limit: float = float('inf')) -> Dict[str, Any]:
        """Processes winning clusters, updates meter points, pops winning cells, and handles gravity drop."""
        total_spin_win = 0.0
        cascade_history = []

        while True:
            clusters = self.find_clusters()
            if not clusters:
                break

            cascade_win = 0.0
            popped_coords = set()

            for cluster in clusters:
                cluster_multiplier = 1
                for r, c in cluster['coords']:
                    popped_coords.add((r, c))
                    if self.grid_state[r][c] == WILD_SYMBOL and self.wild_multipliers[r][c] > cluster_multiplier:
                        cluster_multiplier = self.wild_multipliers[r][c]

                win_amount = self.calculate_cluster_win(cluster['symbol'], len(cluster['coords']))
                cascade_win += (win_amount * cluster_multiplier)

                # Charge Meter Calculations
                if is_bonus_mode:
                    self.meter_points += round(len(cluster['coords']) * 0.55)
                else:
                    is_enhancer = (active_feature_mode == 'EXTRA_CHANCE')
                    meter_multiplier = 0.72 if is_enhancer else 0.48
                    self.meter_points += round(len(cluster['coords']) * meter_multiplier)

            total_spin_win += cascade_win

            # Max Win Cap Check
            if total_spin_win >= max_win_limit:
                total_spin_win = max_win_limit
                cascade_history.append({'clusters': clusters, 'win': cascade_win, 'max_cap_hit': True})
                break

            cascade_history.append({'clusters': clusters, 'win': cascade_win, 'max_cap_hit': False})

            # Pop cells and clear multiplier
            for r, c in popped_coords:
                self.grid_state[r][c] = ''
                self.wild_multipliers[r][c] = 1

            self.mega_wild_region = None

            # Apply Gravity and Drop New Symbols
            for c in range(COLS):
                empty_spaces = 0
                for r in range(ROWS - 1, -1, -1):
                    if self.grid_state[r][c] == '':
                        empty_spaces += 1
                    elif empty_spaces > 0:
                        self.grid_state[r + empty_spaces][c] = self.grid_state[r][c]
                        self.wild_multipliers[r + empty_spaces][c] = self.wild_multipliers[r][c]
                        self.grid_state[r][c] = ''
                        self.wild_multipliers[r][c] = 1

                for r in range(empty_spaces):
                    self.grid_state[r][c] = self.get_random_symbol(is_low_win_prob=not is_bonus_mode)
                    self.wild_multipliers[r][c] = 1

        return {
            'total_win': total_spin_win,
            'cascade_history': cascade_history,
            'meter_points': min(self.meter_points, 100)
        }

    def run_single_spin(self, special_mode: Optional[str] = None, active_feature_mode: Optional[str] = None, max_win_limit: float = float('inf')) -> Dict[str, Any]:
        """Runs a single board generation, applies special modes/wilds, and resolves cascades."""
        is_base_spin = (special_mode is None or special_mode == 'EXTRA_CHANCE')
        self.mega_wild_region = None

        # Fill grid
        for r in range(ROWS):
            for c in range(COLS):
                self.grid_state[r][c] = self.get_random_symbol(is_low_win_prob=is_base_spin)
                self.wild_multipliers[r][c] = 1

        # Determine Mega Wild Spawns based on modes
        if special_mode == 'REGULAR_BONUS':
            if random.random() < 0.45:
                size_map = {4: 5, 3: 4, 2: 3, 1: 2}
                self.spawn_mega_wild(size_map.get(self.bonus_level, 2))
        elif special_mode == 'WILD_HAVOC_SPIN':
            self.spawn_mega_wild(2)
        elif special_mode == 'SUPER_BONUS':
            if random.random() < 0.60:
                size_map = {4: 5, 3: 4, 2: 3, 1: 3}
                self.spawn_mega_wild(size_map.get(self.bonus_level, 3))
        else:
            wild_prob = 0.06 if active_feature_mode == 'EXTRA_CHANCE' else 0.04
            if random.random() < wild_prob:
                self.spawn_mega_wild(2)

        is_slow_mode = special_mode in ['REGULAR_BONUS', 'SUPER_BONUS']
        return self.process_cascades(is_bonus_mode=is_slow_mode, active_feature_mode=active_feature_mode, max_win_limit=max_win_limit)

    def execute_bonus_game(self, special_mode: str = 'REGULAR_BONUS', current_win_so_far: float = 0.0) -> Dict[str, Any]:
        """Executes a full Bonus Session (Free Spins + Level Upgrades + Cap Tracking)."""
        self.meter_points = 0
        self.bonus_level = 2 if special_mode == 'SUPER_BONUS' else 1
        
        cumulative_bonus_win = 0.0
        max_win_amount = self.base_bet * MAX_WIN_CAP
        total_spins = 5
        spin_count = 1
        spin_results = []

        while spin_count <= total_spins:
            remaining_cap = max_win_amount - (current_win_so_far + cumulative_bonus_win)
            result = self.run_single_spin(special_mode=special_mode, max_win_limit=remaining_cap)
            spin_win = result['total_win']
            cumulative_bonus_win += spin_win

            spin_results.append({
                'spin_index': spin_count,
                'total_spins': total_spins,
                'bonus_level': self.bonus_level,
                'win': spin_win,
                'grid_snapshot': [row[:] for row in self.grid_state]
            })

            # Check Max Win Hit
            if (current_win_so_far + cumulative_bonus_win) >= max_win_amount:
                cumulative_bonus_win = max_win_amount - current_win_so_far
                return {
                    'total_bonus_win': cumulative_bonus_win,
                    'spins_executed': spin_count,
                    'max_win_reached': True,
                    'spin_details': spin_results
                }

            # Meter Upgrade Check
            if self.meter_points >= 100 and self.bonus_level < 4:
                self.bonus_level += 1
                total_spins += 4
                self.meter_points = 0

            spin_count += 1

        return {
            'total_bonus_win': cumulative_bonus_win,
            'spins_executed': spin_count - 1,
            'max_win_reached': False,
            'spin_details': spin_results
        }

    def start_spin(self, cost_multiplier: float = 1.0, special_mode: Optional[str] = None, active_feature_mode: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point to execute a paid spin/buy feature action."""
        actual_cost = self.base_bet * cost_multiplier
        max_win_amount = self.base_bet * MAX_WIN_CAP

        if self.balance < actual_cost:
            return {'error': 'INSUFFICIENT_BALANCE', 'balance': self.balance, 'required': actual_cost}

        self.balance -= actual_cost
        self.meter_points = 0
        self.bonus_level = 1

        cumulative_win = 0.0
        bonus_data = None

        if special_mode in ['REGULAR_BONUS', 'SUPER_BONUS']:
            bonus_data = self.execute_bonus_game(special_mode=special_mode, current_win_so_far=0.0)
            cumulative_win = bonus_data['total_bonus_win']
        else:
            spin_res = self.run_single_spin(special_mode=special_mode, active_feature_mode=active_feature_mode, max_win_limit=max_win_amount)
            cumulative_win = spin_res['total_win']

            # Trigger Bonus naturally if Charge Meter reaches 100 PTS
            if cumulative_win < max_win_amount and self.meter_points >= 100 and (special_mode is None or special_mode == 'EXTRA_CHANCE'):
                bonus_data = self.execute_bonus_game(special_mode='REGULAR_BONUS', current_win_so_far=cumulative_win)
                cumulative_win += bonus_data['total_bonus_win']

        if cumulative_win > max_win_amount:
            cumulative_win = max_win_amount

        self.balance += cumulative_win

        return {
            'cost': actual_cost,
            'payout': cumulative_win,
            'net_gain': cumulative_win - actual_cost,
            'new_balance': self.balance,
            'meter_points': min(self.meter_points, 100),
            'bonus_data': bonus_data,
            'final_grid': [row[:] for row in self.grid_state]
        }


# ==========================================
# EXAMPLE USAGE & TESTS
# ==========================================
if __name__ == '__main__':
    engine = WildHavocGameEngine(initial_balance=10000.0, bet_index=3)

    print("=== Testing Base Spin ===")
    res_base = engine.start_spin(cost_multiplier=1.0)
    print(f"Cost: ${res_base['cost']:.2f} | Payout: ${res_base['payout']:.2f} | Balance: ${res_base['new_balance']:.2f}")

    print("\n=== Testing Regular Bonus Buy (100x) ===")
    res_bonus = engine.start_spin(cost_multiplier=100.0, special_mode='REGULAR_BONUS')
    print(f"Cost: ${res_bonus['cost']:.2f} | Total Bonus Win: ${res_bonus['payout']:.2f} | Balance: ${res_bonus['new_balance']:.2f}")

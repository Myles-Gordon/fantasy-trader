# FantasyTrader

A command-line tool that analyzes your fantasy football league and surfaces trade opportunities — either automatically or by looking up players of similar value.

## Features

- **Automatic trade finder** — compares your roster against league averages, identifies your weak and surplus positions, and proposes fair 1-for-1 and package trades (2-for-1, 1-for-2) where both sides benefit
- **Similar players lookup** — pick any player on your roster and see players of comparable value on other teams, useful when you already have a trade partner in mind
- **Team overview** — after the trade finder runs, get a position-by-position ranking vs the league average with a plain-English verdict on whether trading is worthwhile

League settings (dynasty/redraft, PPR scoring, team count, superflex) are pulled directly from the Sleeper API — no manual configuration needed.

## Requirements

- Python 3.8+
- A [Sleeper](https://sleeper.com) account in at least one fantasy football league

## Installation

```bash
git clone https://github.com/your-username/FantasyTrader.git
cd FantasyTrader
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

You will be prompted to:

1. Enter your Sleeper username
2. Select a league from your active leagues
3. Choose a mode

### Mode 1 — Automatic trade finder

```
How many trade proposals to show [10]:
Max trade value imbalance % (e.g. 10 = within 10%) [10]:
```

Outputs:
- Your full roster sorted by value
- Position weaknesses vs league average
- Top 1-for-1 trade proposals
- Top package trade proposals (2-for-1 and 1-for-2)
- Team overview with a trading recommendation

### Mode 2 — Similar players lookup

```
Value match tolerance % (e.g. 20 = within 20% of player's value) [20]:
```

Shows your roster and lets you pick a player. Returns all players on other teams within the value tolerance, sorted by closest value first, with their team and starter/bench role.

After each mode completes you are returned to the menu to run another search or exit.

## How it works

Player values are fetched from [FantasyCalc](https://fantasycalc.com) and matched against Sleeper roster data. Trade fairness is measured as the percentage value difference between the players involved. Trade proposals are only surfaced when both teams improve their starter value and the deal closes at least 20% of the receiving team's positional deficit.

Sleeper player data is cached locally for 24 hours to reduce API calls on repeated runs.

## Data sources

- [Sleeper API](https://docs.sleeper.com) — rosters, users, league settings
- [FantasyCalc API](https://fantasycalc.com) — player values (redraft and dynasty, PPR/half-PPR/standard)

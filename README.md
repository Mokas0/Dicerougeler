# The Rolling Bones Tavern

A dice-rolling roguelike game set in a dangerous tavern where the only way out is to beat every gambler at their own game.

## How to Play

```bash
python3 dice_roguelike.py
```

## Game Overview

You've wandered into the roughest tavern in the realm. The only way out? Beat every gambler at their own game. Win and advance. Lose... and you don't leave.

### Core Mechanics

- **Roll dice** against opponents - highest total wins
- **Win** to earn gold and advance
- **Lose** = Game Over (it's a roguelike!)
- **Defeat 5 bosses** to win the game

### The Shop

Between fights, visit the bar to buy:

**Items (Permanent Upgrades):**
- Extra dice
- Loaded dice (minimum roll values)
- Exploding dice (max rolls add bonus dice)
- Rerolls
- Gold multipliers
- And more!

**Consumables (One-time Use):**
- Drinks that boost your rolls
- See enemy rolls before you roll
- Guaranteed win potions
- Temporary extra dice

### Bosses

Each boss has unique mechanics:

1. **The Card Sharp** - Rerolls any die below 4
2. **Iron Ingrid** - Adds her lowest die twice
3. **The Phantom Gambler** - All dice explode on 6+
4. **Baron Von Chance** - Rolls twice, keeps higher total
5. **THE BARKEEP** - The final challenge with multiple abilities

### Tips

- Save consumables for boss fights
- Some items combo well together (exploding dice + extra dice = powerful)
- Rerolls can save your life - use them wisely
- Build toward a strategy: glass cannon with many dice, or consistency with minimum rolls

## Requirements

- Python 3.6+
- Terminal with Unicode support (for dice art)

## Controls

- Number keys to select options
- ENTER to confirm/continue

Good luck, gambler. May your dice roll high!

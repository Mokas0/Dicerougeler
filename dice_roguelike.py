#!/usr/bin/env python3
"""
🎲 THE ROLLING BONES TAVERN 🎲
A Dice Rolling Roguelike

Roll the dice, win gold, buy drinks, defeat patrons, and challenge the bosses!
One wrong roll and you're out cold on the tavern floor...
"""

import random
import time
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def slow_print(text, delay=0.03):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def press_enter():
    input("\n[Press ENTER to continue...]")

def roll_die(sides=6, minimum=1):
    """Roll a single die with optional minimum value."""
    return max(minimum, random.randint(1, sides))

def display_dice_roll(rolls: List[int], label=""):
    """Display dice rolls with ASCII art."""
    dice_art = {
        1: ["┌─────┐", "│     │", "│  ●  │", "│     │", "└─────┘"],
        2: ["┌─────┐", "│ ●   │", "│     │", "│   ● │", "└─────┘"],
        3: ["┌─────┐", "│ ●   │", "│  ●  │", "│   ● │", "└─────┘"],
        4: ["┌─────┐", "│ ● ● │", "│     │", "│ ● ● │", "└─────┘"],
        5: ["┌─────┐", "│ ● ● │", "│  ●  │", "│ ● ● │", "└─────┘"],
        6: ["┌─────┐", "│ ● ● │", "│ ● ● │", "│ ● ● │", "└─────┘"],
    }

    if label:
        print(f"\n{label}")

    # Handle rolls > 6 by capping display at 6
    display_rolls = [min(r, 6) for r in rolls]

    for line in range(5):
        row = "  ".join(dice_art[r][line] for r in display_rolls)
        print(f"  {row}")

    print(f"  Values: {rolls} = {sum(rolls)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ITEMS AND CONSUMABLES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Item:
    name: str
    description: str
    cost: int
    effect: str  # Description of passive effect

    # Stat modifiers
    extra_dice: int = 0
    dice_sides: int = 0  # Extra sides on dice (d6 -> d8, etc.)
    min_roll: int = 0    # Minimum value on each die
    rerolls: int = 0     # Number of rerolls per combat
    gold_multiplier: float = 1.0
    damage_reduction: int = 0
    bonus_damage: int = 0

    # Special flags
    exploding_dice: bool = False  # 6s roll again
    double_or_nothing: bool = False
    steal_dice: bool = False  # Steal enemy's lowest die


ITEMS = [
    Item(
        name="Loaded Die",
        description="A suspiciously heavy die that never rolls below 3",
        cost=50,
        effect="All dice roll minimum 3",
        min_roll=3
    ),
    Item(
        name="Extra Bones",
        description="A spare die you found under a table",
        cost=40,
        effect="+1 die per roll",
        extra_dice=1
    ),
    Item(
        name="Lucky Rabbit's Foot",
        description="Still warm... and twitching occasionally",
        cost=60,
        effect="+1 reroll per combat",
        rerolls=1
    ),
    Item(
        name="Gambler's Gloves",
        description="Worn leather gloves with weighted fingertips",
        cost=75,
        effect="All dice roll minimum 2, +1 reroll",
        min_roll=2,
        rerolls=1
    ),
    Item(
        name="The Bigger Die",
        description="An oversized d8 that barely fits in your hand",
        cost=80,
        effect="Roll d8s instead of d6s",
        dice_sides=2
    ),
    Item(
        name="Thief's Fingers",
        description="Nimble gloves that let you... borrow... dice",
        cost=100,
        effect="Steal enemy's lowest die result",
        steal_dice=True
    ),
    Item(
        name="Explosive Dice Set",
        description="Dice that explode! (figuratively... mostly)",
        cost=90,
        effect="Rolling max explodes (roll again, add result)",
        exploding_dice=True
    ),
    Item(
        name="Double Down Token",
        description="A cursed coin - double your roll or get nothing",
        cost=70,
        effect="50% chance to double total, 50% to halve it",
        double_or_nothing=True
    ),
    Item(
        name="Barkeep's Favor",
        description="The barkeep slips you extra winnings",
        cost=65,
        effect="+50% gold from victories",
        gold_multiplier=1.5
    ),
    Item(
        name="Brass Knuckles",
        description="For when dice aren't convincing enough",
        cost=55,
        effect="+3 to final roll total",
        bonus_damage=3
    ),
    Item(
        name="Leather Duster",
        description="A weathered coat that's seen many bar fights",
        cost=45,
        effect="-2 from enemy roll totals",
        damage_reduction=2
    ),
    Item(
        name="The House Edge",
        description="A mysterious artifact - the house always wins",
        cost=150,
        effect="+2 dice, all roll minimum 2",
        extra_dice=2,
        min_roll=2
    ),
]


@dataclass
class Consumable:
    name: str
    description: str
    cost: int
    effect_description: str

    # Effects
    heal: int = 0
    temp_extra_dice: int = 0
    temp_min_roll: int = 0
    temp_rerolls: int = 0
    guarantee_win: bool = False
    see_enemy_roll: bool = False
    add_to_roll: int = 0
    multiply_roll: float = 1.0


CONSUMABLES = [
    Consumable(
        name="Cheap Whiskey",
        description="Burns going down, steadies the hand",
        cost=10,
        effect_description="Add +2 to your roll this combat",
        add_to_roll=2
    ),
    Consumable(
        name="Dwarven Stout",
        description="Thick enough to stand a spoon in",
        cost=20,
        effect_description="+1 temporary die this combat",
        temp_extra_dice=1
    ),
    Consumable(
        name="Elven Wine",
        description="Sharpens the senses... and the ego",
        cost=25,
        effect_description="See enemy's roll before you roll",
        see_enemy_roll=True
    ),
    Consumable(
        name="Dragon's Breath Ale",
        description="WARNING: Extremely flammable",
        cost=35,
        effect_description="All dice minimum 4 this combat",
        temp_min_roll=4
    ),
    Consumable(
        name="Liquid Courage",
        description="A mysterious purple concoction",
        cost=30,
        effect_description="+3 rerolls this combat",
        temp_rerolls=3
    ),
    Consumable(
        name="The Good Stuff",
        description="Top shelf. Reserved for special occasions.",
        cost=50,
        effect_description="+2 dice, all minimum 3 this combat",
        temp_extra_dice=2,
        temp_min_roll=3
    ),
    Consumable(
        name="Barkeep's Special",
        description="'Trust me,' he says with a wink",
        cost=75,
        effect_description="Automatically win this combat",
        guarantee_win=True
    ),
    Consumable(
        name="Snake Oil",
        description="Guaranteed* to work! (*not guaranteed)",
        cost=15,
        effect_description="50% chance to double roll, 50% nothing",
        multiply_roll=2.0
    ),
    Consumable(
        name="Coffee (Black)",
        description="For when you need to sober up, fast",
        cost=5,
        effect_description="+1 reroll this combat",
        temp_rerolls=1
    ),
    Consumable(
        name="Mystery Meat Sandwich",
        description="Don't ask what's in it",
        cost=8,
        effect_description="Add +4 to your roll",
        add_to_roll=4
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ENEMIES AND BOSSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Enemy:
    name: str
    description: str
    dice_count: int
    dice_sides: int = 6
    min_roll: int = 1
    gold_reward: int = 10
    taunt: str = ""
    defeat_text: str = ""

    # Special abilities
    reroll_ones: bool = False
    exploding_dice: bool = False
    steals_item_on_win: bool = False

    # Boss-specific
    is_boss: bool = False
    boss_ability: str = ""
    phase_two_threshold: float = 0.0  # Activates special ability below this roll %


REGULAR_ENEMIES = [
    Enemy(
        name="Tipsy Farmer",
        description="A local who's had a few too many",
        dice_count=2,
        gold_reward=15,
        taunt="*hic* I'll show ya how we roll in the fields!",
        defeat_text="The farmer slumps over, muttering about crops."
    ),
    Enemy(
        name="Traveling Merchant",
        description="A shifty dealer who wants to 'test the local games'",
        dice_count=2,
        min_roll=2,
        gold_reward=25,
        taunt="Let me show you some... exotic rolling techniques.",
        defeat_text="The merchant grumbles and counts out your winnings."
    ),
    Enemy(
        name="Off-Duty Guard",
        description="Still in uniform, definitely not supposed to be here",
        dice_count=3,
        gold_reward=30,
        taunt="This stays between us. Now roll!",
        defeat_text="The guard nervously looks around and pays up."
    ),
    Enemy(
        name="Grizzled Veteran",
        description="Scarred hands that have rolled countless dice",
        dice_count=3,
        min_roll=2,
        gold_reward=35,
        taunt="I've won wars with worse odds, kid.",
        defeat_text="The veteran nods respectfully and slides over the gold."
    ),
    Enemy(
        name="Cocky Noble",
        description="Slumming it with the commoners for 'thrills'",
        dice_count=2,
        dice_sides=8,
        gold_reward=50,
        taunt="I'll have you know these dice are imported!",
        defeat_text="The noble huffs indignantly and throws gold at you."
    ),
    Enemy(
        name="Mysterious Stranger",
        description="Hood up, face hidden, dice ready",
        dice_count=3,
        reroll_ones=True,
        gold_reward=40,
        taunt="...",
        defeat_text="The stranger silently pushes coins across the table."
    ),
    Enemy(
        name="Boisterous Bard",
        description="Somehow narrating the game while playing",
        dice_count=3,
        gold_reward=35,
        taunt="🎵 A roll of the dice, a twist of fate! 🎵",
        defeat_text="The bard composes a sad ballad about their loss."
    ),
    Enemy(
        name="Retired Pirate",
        description="One eye, one hand, but a pocket full of dice",
        dice_count=4,
        min_roll=1,
        gold_reward=45,
        taunt="Arrr! I've gambled with sea serpents, ye scallywag!",
        defeat_text="The pirate laughs heartily and pays their debt."
    ),
    Enemy(
        name="Nervous Apprentice",
        description="A young wizard trying to act cool",
        dice_count=2,
        exploding_dice=True,
        gold_reward=30,
        taunt="I-I've enchanted these dice! Probably!",
        defeat_text="The apprentice's dice fizzle out as they pay up."
    ),
    Enemy(
        name="Dwarf Miner",
        description="Fresh from the mines with gold to burn",
        dice_count=3,
        dice_sides=6,
        min_roll=2,
        gold_reward=55,
        taunt="I dig up gold, I don't give it away! Let's roll!",
        defeat_text="The dwarf grumbles in their beard but honors the bet."
    ),
]


BOSSES = [
    Enemy(
        name="The Card Sharp",
        description="A legendary cheat who's never been caught",
        dice_count=4,
        dice_sides=6,
        min_roll=3,
        gold_reward=100,
        taunt="The house always wins, friend. And I AM the house.",
        defeat_text="For the first time, the Card Sharp looks genuinely surprised.",
        is_boss=True,
        boss_ability="Rerolls any die showing less than 4",
    ),
    Enemy(
        name="Iron Ingrid",
        description="The arm-wrestling champion turned dice queen",
        dice_count=5,
        dice_sides=6,
        gold_reward=125,
        taunt="I've broken arms and spirits. Your dice are next!",
        defeat_text="Ingrid crushes her mug in frustration, but pays up.",
        is_boss=True,
        boss_ability="Adds her lowest die a second time",
        reroll_ones=True
    ),
    Enemy(
        name="The Phantom Gambler",
        description="Some say he died at this table years ago...",
        dice_count=4,
        dice_sides=8,
        gold_reward=150,
        taunt="I've got nothing to lose... I've already lost everything.",
        defeat_text="The Phantom fades slightly, a ghostly smile forming.",
        is_boss=True,
        boss_ability="All dice explode on 6+",
        exploding_dice=True
    ),
    Enemy(
        name="Baron Von Chance",
        description="A nobleman who wagered his soul on dice",
        dice_count=4,
        dice_sides=6,
        min_roll=2,
        gold_reward=175,
        taunt="Luck? There's no such thing. Only DESTINY!",
        defeat_text="The Baron laughs maniacally even in defeat.",
        is_boss=True,
        boss_ability="Rolls twice, keeps the higher total",
    ),
    Enemy(
        name="THE BARKEEP",
        description="The final challenge. He's seen every trick.",
        dice_count=5,
        dice_sides=8,
        min_roll=2,
        gold_reward=500,
        taunt="You've beaten my best customers. Now face ME.",
        defeat_text="The Barkeep smiles. 'Well played. The tavern is yours.'",
        is_boss=True,
        boss_ability="Copies your best item's effect, +2 to all dice",
        reroll_ones=True,
        exploding_dice=True
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# PLAYER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Player:
    gold: int = 50
    base_dice: int = 2
    base_sides: int = 6
    items: List[Item] = field(default_factory=list)
    consumables: List[Consumable] = field(default_factory=list)
    wins: int = 0
    current_floor: int = 1

    def get_total_dice(self) -> int:
        return self.base_dice + sum(item.extra_dice for item in self.items)

    def get_dice_sides(self) -> int:
        return self.base_sides + sum(item.dice_sides for item in self.items)

    def get_min_roll(self) -> int:
        mins = [item.min_roll for item in self.items if item.min_roll > 0]
        return max(mins) if mins else 1

    def get_rerolls(self) -> int:
        return sum(item.rerolls for item in self.items)

    def get_gold_multiplier(self) -> float:
        mult = 1.0
        for item in self.items:
            mult *= item.gold_multiplier
        return mult

    def get_bonus_damage(self) -> int:
        return sum(item.bonus_damage for item in self.items)

    def get_damage_reduction(self) -> int:
        return sum(item.damage_reduction for item in self.items)

    def has_exploding_dice(self) -> bool:
        return any(item.exploding_dice for item in self.items)

    def has_steal_dice(self) -> bool:
        return any(item.steal_dice for item in self.items)

    def has_double_or_nothing(self) -> bool:
        return any(item.double_or_nothing for item in self.items)

# ═══════════════════════════════════════════════════════════════════════════════
# GAME CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class DiceRoguelike:
    def __init__(self):
        self.player = Player()
        self.enemies_defeated = 0
        self.bosses_defeated = 0
        self.current_enemy_pool = []
        self.game_over = False
        self.victory = False

    def title_screen(self):
        clear_screen()
        title = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     🎲🎲🎲   THE ROLLING BONES TAVERN   🎲🎲🎲                                ║
║                                                                               ║
║           ██████╗  ██████╗ ██╗     ██╗     ██╗███╗   ██╗ ██████╗              ║
║           ██╔══██╗██╔═══██╗██║     ██║     ██║████╗  ██║██╔════╝              ║
║           ██████╔╝██║   ██║██║     ██║     ██║██╔██╗ ██║██║  ███╗             ║
║           ██╔══██╗██║   ██║██║     ██║     ██║██║╚██╗██║██║   ██║             ║
║           ██║  ██║╚██████╔╝███████╗███████╗██║██║ ╚████║╚██████╔╝             ║
║           ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝              ║
║                                                                               ║
║           ██████╗  ██████╗ ███╗   ██╗███████╗███████╗                         ║
║           ██╔══██╗██╔═══██╗████╗  ██║██╔════╝██╔════╝                         ║
║           ██████╔╝██║   ██║██╔██╗ ██║█████╗  ███████╗                         ║
║           ██╔══██╗██║   ██║██║╚██╗██║██╔══╝  ╚════██║                         ║
║           ██████╔╝╚██████╔╝██║ ╚████║███████╗███████║                         ║
║           ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚══════╝                         ║
║                                                                               ║
║                    ~ A Dice Rolling Roguelike ~                               ║
║                                                                               ║
║       You've wandered into the roughest tavern in the realm.                  ║
║       The only way out? Beat every gambler at their own game.                 ║
║       Win and advance. Lose... and you don't leave.                           ║
║                                                                               ║
║                       [1] New Game                                            ║
║                       [2] How to Play                                         ║
║                       [3] Quit                                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        print(title)

    def show_tutorial(self):
        clear_screen()
        tutorial = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           HOW TO PLAY                                         ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  THE BASICS:                                                                  ║
║  • You and your opponent both roll dice                                       ║
║  • Highest total wins!                                                        ║
║  • Win = earn gold and advance                                                ║
║  • Lose = GAME OVER (this is a roguelike after all)                          ║
║                                                                               ║
║  PROGRESSION:                                                                 ║
║  • Defeat regular patrons to earn gold                                        ║
║  • Every few wins, face a BOSS with special abilities                         ║
║  • Beat all 5 bosses to win the game!                                         ║
║                                                                               ║
║  THE SHOP:                                                                    ║
║  • Between fights, visit the bar to buy:                                      ║
║    - ITEMS: Permanent upgrades (more dice, loaded dice, etc.)                 ║
║    - CONSUMABLES: One-time use items for tough fights                         ║
║                                                                               ║
║  TIPS:                                                                        ║
║  • Save consumables for boss fights!                                          ║
║  • Some items combo well together                                             ║
║  • Rerolls can save your life - use them wisely                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        print(tutorial)
        press_enter()

    def show_status(self):
        print("\n" + "═" * 60)
        print(f"  💰 Gold: {self.player.gold}  |  🎲 Dice: {self.player.get_total_dice()}d{self.player.get_dice_sides()}  |  🏆 Wins: {self.player.wins}")
        print(f"  📊 Floor: {self.player.current_floor}  |  👹 Bosses Defeated: {self.bosses_defeated}/5")
        if self.player.items:
            item_names = ", ".join(item.name for item in self.player.items)
            print(f"  🎒 Items: {item_names}")
        if self.player.consumables:
            cons_names = ", ".join(c.name for c in self.player.consumables)
            print(f"  🍺 Consumables: {cons_names}")
        print("═" * 60)

    def roll_dice(self, count: int, sides: int, min_roll: int = 1,
                  exploding: bool = False, temp_min: int = 0) -> List[int]:
        """Roll dice with all modifiers applied."""
        actual_min = max(min_roll, temp_min)
        rolls = []

        for _ in range(count):
            roll = roll_die(sides, actual_min)
            rolls.append(roll)

            # Handle exploding dice
            if exploding and roll == sides:
                extra_roll = roll_die(sides, actual_min)
                rolls.append(extra_roll)
                # Keep exploding!
                while extra_roll == sides:
                    extra_roll = roll_die(sides, actual_min)
                    rolls.append(extra_roll)

        return rolls

    def enemy_roll(self, enemy: Enemy) -> List[int]:
        """Handle enemy rolling with their abilities."""
        rolls = self.roll_dice(
            enemy.dice_count,
            enemy.dice_sides,
            enemy.min_roll,
            enemy.exploding_dice
        )

        # Special abilities
        if enemy.reroll_ones:
            rolls = [roll_die(enemy.dice_sides, 2) if r == 1 else r for r in rolls]

        # Boss abilities
        if enemy.is_boss:
            if enemy.name == "The Card Sharp":
                # Reroll anything below 4
                rolls = [roll_die(enemy.dice_sides, 4) if r < 4 else r for r in rolls]
            elif enemy.name == "Iron Ingrid":
                # Add lowest die again
                rolls.append(min(rolls))
            elif enemy.name == "Baron Von Chance":
                # Roll twice, keep higher
                second_rolls = self.roll_dice(enemy.dice_count, enemy.dice_sides, enemy.min_roll)
                if sum(second_rolls) > sum(rolls):
                    rolls = second_rolls

        return rolls

    def combat(self, enemy: Enemy) -> bool:
        """Run a combat encounter. Returns True if player wins."""
        clear_screen()
        print("\n" + "╔" + "═" * 58 + "╗")
        print(f"║  CHALLENGER: {enemy.name:44} ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  {enemy.description:56} ║")
        print(f"║  Dice: {enemy.dice_count}d{enemy.dice_sides}" + " " * 46 + "║")
        if enemy.is_boss:
            print(f"║  ⚠️  BOSS ABILITY: {enemy.boss_ability:37} ║")
        print("╚" + "═" * 58 + "╝")

        if enemy.taunt:
            print(f'\n  "{enemy.taunt}"')

        self.show_status()

        # Check for consumables to use
        used_consumable = None
        temp_dice = 0
        temp_min = 0
        temp_rerolls = 0
        add_to_roll = 0
        multiply_roll = 1.0
        see_enemy = False
        auto_win = False

        if self.player.consumables:
            print("\n  Use a consumable? (Enter number, or 0 for none)")
            for i, cons in enumerate(self.player.consumables, 1):
                print(f"    [{i}] {cons.name}: {cons.effect_description}")
            print(f"    [0] No consumable")

            choice = input("\n  Your choice: ").strip()
            if choice.isdigit() and 0 < int(choice) <= len(self.player.consumables):
                used_consumable = self.player.consumables.pop(int(choice) - 1)
                print(f"\n  🍺 You use {used_consumable.name}!")

                temp_dice = used_consumable.temp_extra_dice
                temp_min = used_consumable.temp_min_roll
                temp_rerolls = used_consumable.temp_rerolls
                add_to_roll = used_consumable.add_to_roll
                see_enemy = used_consumable.see_enemy_roll
                auto_win = used_consumable.guarantee_win

                if used_consumable.multiply_roll != 1.0:
                    if random.random() < 0.5:
                        multiply_roll = used_consumable.multiply_roll
                        print("  The Snake Oil WORKS! Your roll will be doubled!")
                    else:
                        print("  The Snake Oil fizzles... no effect!")

        # If auto-win consumable
        if auto_win:
            print("\n  ✨ The Barkeep's Special guarantees your victory!")
            press_enter()
            print(f"\n  {enemy.defeat_text}")
            return True

        # Show enemy roll first if player can see it
        enemy_rolls = self.enemy_roll(enemy)
        if see_enemy:
            display_dice_roll(enemy_rolls, f"  👁️  You see {enemy.name}'s roll:")
            press_enter()

        # Player roll
        total_dice = self.player.get_total_dice() + temp_dice
        dice_sides = self.player.get_dice_sides()
        min_roll = max(self.player.get_min_roll(), temp_min)
        rerolls = self.player.get_rerolls() + temp_rerolls

        input("\n  Press ENTER to roll your dice...")

        player_rolls = self.roll_dice(
            total_dice,
            dice_sides,
            min_roll,
            self.player.has_exploding_dice()
        )

        display_dice_roll(player_rolls, "  🎲 YOUR ROLL:")

        # Reroll logic
        while rerolls > 0:
            print(f"\n  You have {rerolls} reroll(s) remaining.")
            reroll_choice = input("  Reroll? (y/n): ").strip().lower()
            if reroll_choice == 'y':
                rerolls -= 1
                player_rolls = self.roll_dice(
                    total_dice,
                    dice_sides,
                    min_roll,
                    self.player.has_exploding_dice()
                )
                display_dice_roll(player_rolls, "  🎲 REROLL:")
            else:
                break

        player_total = sum(player_rolls)

        # Apply bonuses
        player_total += self.player.get_bonus_damage()
        player_total += add_to_roll
        player_total = int(player_total * multiply_roll)

        # Double or nothing
        if self.player.has_double_or_nothing():
            print("\n  🎰 Double or Nothing activates!")
            if random.random() < 0.5:
                player_total *= 2
                print(f"  DOUBLE! Your total is now {player_total}!")
            else:
                player_total //= 2
                print(f"  Halved! Your total is now {player_total}...")

        # Steal dice
        if self.player.has_steal_dice() and enemy_rolls:
            stolen = min(enemy_rolls)
            enemy_rolls.remove(stolen)
            player_total += stolen
            print(f"\n  🤏 You steal a {stolen} from your opponent!")

        # Show enemy roll
        if not see_enemy:
            print("\n  ...")
            time.sleep(1)
            display_dice_roll(enemy_rolls, f"  🎲 {enemy.name.upper()}'S ROLL:")

        enemy_total = sum(enemy_rolls) - self.player.get_damage_reduction()
        enemy_total = max(0, enemy_total)

        print(f"\n  {'═' * 40}")
        print(f"  YOUR TOTAL:  {player_total}")
        print(f"  ENEMY TOTAL: {enemy_total}")
        print(f"  {'═' * 40}")

        time.sleep(1)

        if player_total > enemy_total:
            print("\n  🎉 VICTORY! 🎉")
            return True
        elif player_total == enemy_total:
            print("\n  ⚔️  TIE! Rolling sudden death...")
            time.sleep(1)
            # Sudden death - single die each
            player_sd = roll_die(6)
            enemy_sd = roll_die(6)
            print(f"  You: {player_sd}  |  Enemy: {enemy_sd}")
            if player_sd >= enemy_sd:  # Ties favor player in sudden death
                print("\n  🎉 VICTORY! 🎉")
                return True
            else:
                print("\n  💀 DEFEAT! 💀")
                return False
        else:
            print("\n  💀 DEFEAT! 💀")
            return False

    def shop(self):
        """The tavern shop between fights."""
        while True:
            clear_screen()
            print("\n" + "╔" + "═" * 58 + "╗")
            print("║            🍺 THE BAR 🍺                                 ║")
            print("╠" + "═" * 58 + "╣")
            print("║  The barkeep eyes you. 'What'll it be?'                  ║")
            print("╚" + "═" * 58 + "╝")

            self.show_status()

            print("\n  [1] Buy Items (Permanent)")
            print("  [2] Buy Consumables (One-time use)")
            print("  [3] View your Items")
            print("  [4] Leave the bar")

            choice = input("\n  Your choice: ").strip()

            if choice == "1":
                self.shop_items()
            elif choice == "2":
                self.shop_consumables()
            elif choice == "3":
                self.view_items()
            elif choice == "4":
                break

    def shop_items(self):
        """Browse and buy permanent items."""
        available_items = [i for i in ITEMS if i not in self.player.items]

        if not available_items:
            print("\n  No more items available!")
            press_enter()
            return

        clear_screen()
        print("\n" + "═" * 60)
        print("  ITEMS FOR SALE")
        print("═" * 60)

        for i, item in enumerate(available_items, 1):
            affordable = "✓" if self.player.gold >= item.cost else "✗"
            print(f"\n  [{i}] {item.name} - {item.cost}g [{affordable}]")
            print(f"      {item.description}")
            print(f"      Effect: {item.effect}")

        print(f"\n  [0] Back")
        print(f"\n  Your gold: {self.player.gold}")

        choice = input("\n  Buy which item? ").strip()

        if choice.isdigit() and 0 < int(choice) <= len(available_items):
            item = available_items[int(choice) - 1]
            if self.player.gold >= item.cost:
                self.player.gold -= item.cost
                self.player.items.append(item)
                print(f"\n  ✅ Purchased {item.name}!")
            else:
                print("\n  ❌ Not enough gold!")
            press_enter()

    def shop_consumables(self):
        """Browse and buy consumables."""
        clear_screen()
        print("\n" + "═" * 60)
        print("  DRINKS & FOOD")
        print("═" * 60)

        for i, cons in enumerate(CONSUMABLES, 1):
            affordable = "✓" if self.player.gold >= cons.cost else "✗"
            print(f"\n  [{i}] {cons.name} - {cons.cost}g [{affordable}]")
            print(f"      {cons.description}")
            print(f"      Effect: {cons.effect_description}")

        print(f"\n  [0] Back")
        print(f"\n  Your gold: {self.player.gold}")

        choice = input("\n  Buy which consumable? ").strip()

        if choice.isdigit() and 0 < int(choice) <= len(CONSUMABLES):
            cons = CONSUMABLES[int(choice) - 1]
            if self.player.gold >= cons.cost:
                self.player.gold -= cons.cost
                self.player.consumables.append(Consumable(
                    name=cons.name,
                    description=cons.description,
                    cost=cons.cost,
                    effect_description=cons.effect_description,
                    heal=cons.heal,
                    temp_extra_dice=cons.temp_extra_dice,
                    temp_min_roll=cons.temp_min_roll,
                    temp_rerolls=cons.temp_rerolls,
                    guarantee_win=cons.guarantee_win,
                    see_enemy_roll=cons.see_enemy_roll,
                    add_to_roll=cons.add_to_roll,
                    multiply_roll=cons.multiply_roll
                ))
                print(f"\n  ✅ Purchased {cons.name}!")
            else:
                print("\n  ❌ Not enough gold!")
            press_enter()

    def view_items(self):
        """View owned items and their effects."""
        clear_screen()
        print("\n" + "═" * 60)
        print("  YOUR ITEMS")
        print("═" * 60)

        if not self.player.items:
            print("\n  You don't own any items yet.")
        else:
            for item in self.player.items:
                print(f"\n  📦 {item.name}")
                print(f"     {item.effect}")

        print("\n" + "═" * 60)
        print("  YOUR CONSUMABLES")
        print("═" * 60)

        if not self.player.consumables:
            print("\n  You don't have any consumables.")
        else:
            for cons in self.player.consumables:
                print(f"\n  🍺 {cons.name}")
                print(f"     {cons.effect_description}")

        press_enter()

    def get_next_enemy(self) -> Enemy:
        """Get the next enemy based on progression."""
        # Boss every 4 wins
        if self.player.wins > 0 and self.player.wins % 4 == 0:
            if self.bosses_defeated < len(BOSSES):
                return BOSSES[self.bosses_defeated]

        # Regular enemy - scale difficulty with floor
        available = [e for e in REGULAR_ENEMIES if e.dice_count <= self.player.current_floor + 2]
        if not available:
            available = REGULAR_ENEMIES

        return random.choice(available)

    def game_over_screen(self):
        """Display game over screen."""
        clear_screen()
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                           💀 GAME OVER 💀                                     ║
║                                                                               ║
║              You've lost your last roll at The Rolling Bones.                 ║
║                    The tavern claims another victim...                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """)
        print(f"  Final Stats:")
        print(f"  • Wins: {self.player.wins}")
        print(f"  • Bosses Defeated: {self.bosses_defeated}")
        print(f"  • Gold Earned: {self.player.gold}")
        print(f"  • Items Collected: {len(self.player.items)}")
        press_enter()

    def victory_screen(self):
        """Display victory screen."""
        clear_screen()
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                        🎉🎲 VICTORY! 🎲🎉                                     ║
║                                                                               ║
║         You've defeated the Barkeep and conquered The Rolling Bones!          ║
║                                                                               ║
║              The tavern is yours. The legend of your dice                     ║
║                   will be told for generations to come.                       ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """)
        print(f"  Final Stats:")
        print(f"  • Total Wins: {self.player.wins}")
        print(f"  • All 5 Bosses Defeated!")
        print(f"  • Final Gold: {self.player.gold}")
        print(f"  • Items Collected: {len(self.player.items)}")
        press_enter()

    def run(self):
        """Main game loop."""
        while True:
            self.title_screen()
            choice = input("\n  Your choice: ").strip()

            if choice == "1":
                # Reset for new game
                self.player = Player()
                self.enemies_defeated = 0
                self.bosses_defeated = 0
                self.game_over = False
                self.victory = False

                # Game intro
                clear_screen()
                slow_print("\n  You push open the heavy wooden door...")
                time.sleep(0.5)
                slow_print("  The smell of ale and desperation fills your nostrils.")
                time.sleep(0.5)
                slow_print("  Every eye in the tavern turns to you.")
                time.sleep(0.5)
                slow_print('\n  The barkeep polishes a glass. "Fresh meat, eh?"')
                time.sleep(0.5)
                slow_print('  "You want out? Beat everyone here. Including me."')
                time.sleep(0.5)
                slow_print('  "Lose once... and you stay forever."')
                time.sleep(0.5)
                slow_print("\n  He slides a pair of dice across the bar.")
                slow_print('  "Let\'s see what you\'ve got."')
                press_enter()

                # Main game loop
                while not self.game_over and not self.victory:
                    # Shop phase
                    self.shop()

                    # Combat phase
                    enemy = self.get_next_enemy()

                    if enemy.is_boss:
                        clear_screen()
                        print("\n" + "═" * 60)
                        print("  ⚠️  BOSS FIGHT INCOMING! ⚠️")
                        print("═" * 60)
                        print(f"\n  {enemy.name} approaches the table...")
                        press_enter()

                    won = self.combat(enemy)

                    if won:
                        # Victory rewards
                        gold_earned = int(enemy.gold_reward * self.player.get_gold_multiplier())
                        self.player.gold += gold_earned
                        self.player.wins += 1
                        self.enemies_defeated += 1

                        if enemy.is_boss:
                            self.bosses_defeated += 1
                            self.player.current_floor += 1

                            if self.bosses_defeated >= 5:
                                self.victory = True

                        print(f"\n  💰 You earned {gold_earned} gold!")
                        if enemy.defeat_text:
                            print(f"\n  {enemy.defeat_text}")
                        press_enter()
                    else:
                        self.game_over = True

                # End screens
                if self.victory:
                    self.victory_screen()
                else:
                    self.game_over_screen()

            elif choice == "2":
                self.show_tutorial()
            elif choice == "3":
                clear_screen()
                print("\n  Thanks for playing The Rolling Bones Tavern!")
                print("  May your dice always roll high.\n")
                break


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    game = DiceRoguelike()
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n\n  Game interrupted. Thanks for playing!")
        sys.exit(0)

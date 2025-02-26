import math
from typing import List, Tuple
from enum import Enum


class Path(Enum):
    Hollow = -1
    Ephemeral = 0
    Ascended = 1
    Divine = 2
    Unbound = 3


class Realm(Enum):
    # No Essence
    Hollow = -1

    # Ephemeral Being
    Mortal = 0
    Elite = 1
    Ascendant = 2

    # Ascended Being
    Harold = 3
    Sage = 4
    Hegemon = 5

    # Divine Being
    Monarch = 6
    Imperial = 7
    Transcendent = 8

    # Unbound Being
    Unbound = 9

    def has_progress(self) -> bool:
        return self.value >= 0 and self.value < 9

    def get_path(self) -> Path:
        return Path(self.value // 3)


class RealmProgress(Enum):
    # No Essence
    Hollow = -1

    # Normal
    Low = 0
    Middle = 1
    High = 2


class Stage(Enum):
    # No Essence
    Hollow = -1

    # Mortal
    Body = 0
    Blood = 1
    Mind = 2

    # Elite
    Weaving = 3
    Energy = 4
    Matter = 5

    # Ascendant
    Infusion = 6
    Harmony = 7
    Awakening = 8

    # Harold
    Formation = 9
    Attunement = 10
    Capacity = 11

    # Sage
    Manifestation = 12
    Expansion = 13
    Amplification = 14

    # Hegemon
    Authority = 15
    Synthesis = 16
    Genesis = 17

    # Monarch
    Assimilation = 18
    Dominion = 19
    Convergence = 20

    # Imperial
    Reflection = 21
    Sovereignty = 22
    Unity = 23

    # Transcendent
    Omniscience = 23
    Omnipresence = 25
    Omnipotence = 26

    # Unbound
    Unbound = 27

    def has_steps(self) -> bool:
        return self.value >= 0 and self.value < 27

    def get_realm(self) -> Realm:
        return Realm(self.value // 3)

    def get_path(self) -> Path:
        return Path(self.value // 9)


class Alignment(Enum):
    Primordial = 0
    Celestial = 1
    Infernal = 2
    Abyssal = 3
    Ethereal = 4
    Environmental = 5
    Artificial = 6
    Temporal = 7
    Cardinal = 8


class UserClass(Enum):
    Bug_Girl_Connoisseur = 0
    Greeter = 1
    Jester = 2
    Soul_Healer = 3
    Friendly_Guide = 4
    Deviant = 5
    Social_Butterfly = 6
    Reactionary = 7  #
    Content_Creator = 8
    Conspiracy_Theorist = 9
    Tech_Support = 10
    Storyteller = 11
    Researcher = 12
    Visionary = 13
    Web_Archiver = 14
    Sticker_Collector = 15
    Reader = 16
    GameDev = 17
    Artist = 18

    def get_name(self) -> str:
        return self.name.replace("_", " ")

    def get_alignment(self) -> Alignment:
        return Alignment.Primordial


class ClassProgress:

    def __init__(self, user_class: UserClass):
        self.user_class = user_class
        self.affinity = 0
        self.points = 0
        self.changed = False

    def get_grade(self) -> str:
        return affinity_to_grade(self.affinity)

    def add_points(self, value: int) -> None:
        self.points += value
        self.changed = True


class Essence:
    def __init__(self):
        self.exp = 0
        self.level = 0
        self.classes = []

    def get_class(self, user_class: UserClass, append=True) -> ClassProgress:
        for c in self.classes:
            if c.user_class == user_class:
                return c

        if not append:
            return None

        cl = ClassProgress(user_class)
        self.classes.append(cl)
        return cl

    def get_class_list(self) -> List[ClassProgress]:
        return self.classes

    def get_level(self) -> int:
        return self.level

    def get_exp(self) -> int:
        return self.exp

    def exp_to_next(self) -> int:
        return math.floor(math.pow(10 * (self.level + 1), 1.5) * 3)

    def get_exp_percent(self) -> float:
        exp_to_next = self.exp_to_next()
        return self.exp / exp_to_next

    def get_exp_percent_str(self) -> str:
        return f"{self.get_exp_percent() * 100:.2f}%"

    def __add_exp(self, value: int) -> None:
        self.exp += value

        if self.exp < 0:
            while True:
                if self.level == 0:
                    self.exp = 0
                    return

                self.level -= 1
                self.exp += self.exp_to_next()
            return

        while True:
            exp_to_next = self.exp_to_next()
            if self.exp < exp_to_next:
                break

            self.exp -= exp_to_next
            self.level += 1

        self.level = min(self.level, 244)

    def get_realm(self) -> Realm:
        realm = (self.level - 1) // 27
        return Realm(realm)

    def get_realm_progress(self) -> RealmProgress:
        stage = (self.level - 1) // 9
        return RealmProgress(stage % 3)

    def get_stage(self) -> Stage:
        stage = (self.level - 1) // 9
        return Stage(stage)

    def get_step(self) -> int:
        step = ((self.level - 1) % 9) + 1
        return step

    def get_path(self) -> Path:
        path = (self.level - 1) // 81
        return Path(path)

    def add_points(self, user_class: UserClass, value: int) -> None:
        self.__add_exp(value)

        cl = self.get_class(user_class)
        cl.add_points(value)

        affinities = [c.points for c in self.classes]
        index = self.classes.index(cl)

        max_value = max(affinities)
        exp_values = [math.exp(v - max_value) for v in affinities]
        sum_values = sum(exp_values)

        relative = [v / sum_values for v in exp_values]

        for i, r in enumerate(relative):
            self.classes[i].affinity = r * self.classes[i].points / 100

        self.classes.sort(key=lambda c: c.points, reverse=True)


def affinity_to_grade(value: float) -> str:
    if value < 1:
        return "X"

    l = math.log(value, 3)
    letter = floor(l)
    sign = floor((l - letter) * 3)

    if letter >= 9:
        return "Z"

    letter = ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"][letter]
    sign = ["-", "", "+"][sign]
    return f"{letter}{sign}"

"""
Population dynamics simulator.

This script models a simplified society of men and women with attributes such as
age, partner status, fertility, and mortality. It includes probabilistic rules for:

- Aging and death by sex and age group
- Pair formation and breakups
- Periods of solitude after relationship loss
- Pregnancy likelihood and gestation
- Birth of children with randomized traits

The simulation uses probability tables and random sampling to approximate
biological and social processes over time.
"""

import random              # Library for random numbers and probability distributions
from dataclasses import dataclass   # Decorator to auto-generate methods for simple data classes
from typing import Optional, List, Tuple, Callable   # Type hints: Optional (nullable), List (sequence), Tuple (fixed-size sequence)


def prob_by_age(age, tabla):
    for a, b, p in tabla:
        if a <= age < b:
            return p
    return 0.0


# Probability of death for males by age range (annualized rates)
PROB_MUERTE_H = [(0,12,0.25/12),(12,45,0.1/12),(45,76,0.3/12),(76,126,0.7/12)]

# Probability of death for females by age range (annualized rates)
PROB_MUERTE_M = [(0,12,0.25/12),(12,45,0.15/12),(45,76,0.35/12),(76,126,0.65/12)]

# Probability of pregnancy by age range
PROB_EMBARAZO = [(12,15,0.2),(15,21,0.45),(21,35,0.8),(35,45,0.4),(45,60,0.2),(60,126,0.05)]

# Probability of wanting a partner by age range
PROB_QUERER_PAREJA = [(12,15,0.6),(15,21,0.65),(21,35,0.8),(35,45,0.6),(45,60,0.5),(60,126,0.2)]

# Probability of forming a couple depending on age difference
PROB_FORMAR_PAREJA = [(0,5,0.45),(5,10,0.4),(10,15,0.35),(15,20,0.25),(20,999,0.15)]

# Probability of breakup (constant across ages)
PROB_RUPTURA = 0.2

# Average time spent alone after breakup, by age range (in months)
MEDIA_SOLO = [(12,15,3),(15,21,6),(21,35,6),(35,45,12),(45,60,24),(60,126,48)]

# Raw distribution of number of babies per pregnancy (weights)
_bebes_raw = {1:0.7,2:0.18,3:0.08,4:0.04,5:0.02}

# Normalize so probabilities sum exactly to 1.0
_bebes_total = sum(_bebes_raw.values())
PROB_BEBES = {k: v/_bebes_total for k,v in _bebes_raw.items()}

# Raw distribution of desired number of children
DESEO_RAW = {1:0.6,2:0.75,3:0.35,4:0.2,5:0.1,6:0.016,7:0.016,8:0.016}

# Normalize so probabilities sum exactly to 1.0
total = sum(DESEO_RAW.values())
PROB_DESEO = {k:v/total for k,v in DESEO_RAW.items()}


# RANDOM SAMPLER
class RandomSampler:
    """Utilities for random sampling from probability distributions."""
    
    @staticmethod
    def sample(dic):
        """Sample a value from a dictionary of probabilities."""
        items = list(dic.items())
        if not items:
            raise ValueError("sample() no puede recibir un diccionario vacío")

        total = sum(prob for _, prob in items)
        if total <= 0:
            raise ValueError("sample() requiere probabilidades positivas")

        umbral = random.random() * total
        acumulado = 0.0

        for valor, prob in items:
            acumulado += prob
            if umbral < acumulado:
                return valor

        return items[-1][0]

    @staticmethod
    def lambda_solo(age):
        """Calculate the rate parameter for exponential distribution of solitude time."""
        media = prob_by_age(age, MEDIA_SOLO)
        return 1/media if media > 0 else 0

    @staticmethod
    def sample_exponencial(lmbda):
        """Sample from exponential distribution and convert months to years."""
        if lmbda == 0:
            return 0
        return random.expovariate(lmbda)/12  # Convertir de meses a años
    
    @staticmethod
    def time_step(lam=1.5, min_dias=1, max_anos=5):
        """Return a random time jump (in years) sampled from an exponential
        distribution with rate `lam`, constrained to fall between `min_dias`
        and `max_anos`."""
        min_t = min_dias / 365
        max_t = max_anos

        while True:
            dt = random.expovariate(lam)
            if min_t <= dt <= max_t:
                return dt


# MODELO
@dataclass
class Person:
    """Represents an individual in the population with demographic and social attributes."""
    id: int
    age: float  # años
    sex: str  # 'H' o 'M'
    has_partner: Optional["Person"] = None
    children_count: int = 0
    child_desire_count: int = 1
    desires_partner: bool = False
    time_left_single : float = 0.0  # meses
    time_left_in_pregnancy: float = 0.0  # meses
    is_alive: bool = True

    def age_up (self, time):
        """Age the person by one month."""
        self.age += time
        
        if self.time_left_in_pregnancy > 0:
            self.time_left_in_pregnancy -= time
            if self.time_left_in_pregnancy < 0:
                self.time_left_in_pregnancy = 0
                       
        if self.time_left_single  > 0:
            self.time_left_single  -= time
        elif self.time_left_single  < 0:
            self.time_left_single  = 0
            
    def is_single(self):
        """Check if person is alive, single, and ready for a new relationship."""
        return (
            self.is_alive and
            self.has_partner is None and
            self.time_left_single  <= 0
        )

    def is_able_to_reproduce(self):
        """Check if person can have children based on sex, status, and desires."""
        if not self.is_alive or self.sex != "M":
            return False
        if self.has_partner is None:
            return False
        if self.time_left_in_pregnancy > 0:
            return False
        limite = min(self.child_desire_count, self.has_partner.child_desire_count)
        return self.children_count < limite


# SIMULADOR
class Simulador:
    """Main simulation engine for population dynamics."""

    def __init__(self, H, M):
        """Initialize simulator with H males and M females."""
        self.people: dict[int, Person] = {}
        self.male_group: set[int] = set()
        self.female_group: set[int] = set()
        self.gestation: set[int] = set()
        self.next_id = 0

        # inicialización
        for _ in range(H):
            self.add_person(self.create_person('H'))

        for _ in range(M):
            self.add_person(self.create_person('M'))

    @property
    def population(self):
        """Return list of all living persons in the simulation."""
        return [self.people[i] for i in self.male_group.union(self.female_group)]

    # GESTIONAR PERSONAS ------------------------
    def add_person(self, persona):
        """Add a person to the simulation and track by sex."""
        self.people[persona.id] = persona
        
        if persona.age < 0:
            self.gestation.add(persona.id)
        elif persona.sex == 'H':
            self.male_group.add(persona.id)
        else:
            self.female_group.add(persona.id)

    def create_person(self, sex):
        """Create a new person with random age and desired number of children."""
        p = Person(
            id=self.next_id,
            age=random.uniform(0,100),
            sex=sex,
            child_desire_count=RandomSampler.sample(PROB_DESEO)
        )
        self.next_id += 1
        return p

    def create_baby(self, gest_time):
        """Create a new baby with random sex and gestation time."""
        # Sexo aleatorio: 0 = hombre, 1 = mujer
        sex = 'H' if random.random() < 0.5 else 'M' 

        bebe = Person(
            id=self.next_id,
            age= -gest_time,  # siempre nace con age: - gest_time
            sex=sex,
            child_desire_count=RandomSampler.sample(PROB_DESEO)
        )
        self.next_id += 1
        return bebe

    # CREAR AGENDA -------------------------------
    def build_events_by_type(
        self,
        funcion: Callable,
        lam: float,
        anos_simulacion: float
    ) -> List[Tuple[float, Callable]]:

        t = 0.0
        agenda = []

        while t < anos_simulacion:
            dt = RandomSampler.time_step(lam=lam)
            t += dt

            if t > anos_simulacion:
                break

            agenda.append((t, funcion))

        return agenda

    def build_event_schedule(self, anos_simulacion: float):

        tipos_eventos = [
            (self.handle_deaths, 0.05),
            (self.partner_desire, 1.0),
            (self.handle_breakups, 0.2),
            (self.match_couples, 0.5),
            (self.handle_pregnancies, 0.1),
        ]

        eventos_globales: List[Tuple[float, Callable]] = []

        for funcion, lam in tipos_eventos:
            agenda = self.build_events_by_type(
                funcion=funcion,
                lam=lam,
                anos_simulacion=anos_simulacion
            )
            eventos_globales.extend(agenda)

        # Merge ordenado
        eventos_globales.sort(key=lambda x: x[0])

        return eventos_globales

    def run(self, anos=100):
        """
        Ejecuta la simulación y devuelve historia de población is_alive.
        """

        historia = []
        last_time=0
        agenda_eventos = self.build_event_schedule(anos)

        for t, funcion in agenda_eventos:
            diff = t - last_time
            self.age_people(diff)
            self.update_gestations(diff)
            funcion(diff)
            historia.append(len(self.population))
            last_time = t

        return historia

    # ACTUALIZAR ----------------------------------
    def age_people(self, time):
        """Age all living persons by one month."""
        # 1. age_up 
        for p in self.population:
            p.age_up (time)

    def update_gestations(self, time):
        """Process ongoing gestations and add born babies to the population."""
        # 6.5. Procesar gestaciones: reducir el tiempo restante y crear people cuando llegue a 0
        
        for item in self.gestation.copy():  # Copia para evitar modificar el set durante la iteración
            bebe = self.people[item]
            bebe.age_up (time)

            if bebe.age >= 0:
                # Bebé completó gestación, agregarlo a la población
                self.add_person (bebe)
                self.gestation.discard(bebe.id)  # Quitar de gestación

    # EVENTOS -------------------------------------
    def handle_deaths(self, time):
        """Apply mortality and handle relationship dissolution from deaths."""
        # 2. muerte

        for p in self.population:

            tabla = PROB_MUERTE_H if p.sex == 'H' else PROB_MUERTE_M
            if random.random() < prob_by_age(p.age, tabla):
                p.is_alive = False

                if p.has_partner:
                    has_partner = p.has_partner
                    has_partner.has_partner = None
                    has_partner.time_left_single  = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(has_partner.age))
                    p.has_partner = None
                
                if p.sex == 'H':
                    self.male_group.discard(p.id)
                else:
                    self.female_group.discard(p.id)

    def partner_desire(self, time):
        """Update desire for partnership based on age and availability."""
        # 4. deseo de has_partner
        for p in self.population:
            if p.is_single():
                p.desires_partner = random.random() < prob_by_age(p.age, PROB_QUERER_PAREJA)

    def match_couples(self, time):
        """Match available individuals who desire partnerships based on age compatibility."""
        # Filtrar people disponibles y con deseo de has_partner
        male_group = [self.people[i] for i in self.male_group if self.people[i].is_single() and self.people[i].desires_partner]
        female_group = [self.people[i] for i in self.female_group if self.people[i].is_single() and self.people[i].desires_partner]

        random.shuffle(male_group)
        random.shuffle(female_group)

        for h in male_group:
            # Cada hombre intenta con varias female_group, no solo con la mejor
            for m in female_group:
                if not m.is_single():
                    continue

                diff = abs(h.age - m.age)
                p = prob_by_age(diff, PROB_FORMAR_PAREJA)

                # Aumentar probabilidad de éxito multiplicando por un factor
                if random.random() < p:  # factor > 1 aumenta colisiones
                    h.has_partner = m
                    m.has_partner = h
                    break  # salir del bucle, ya emparejado

    def handle_breakups(self, time):
        """Randomly dissolve some partnerships and set solitude recovery time."""
        # 6. rupturas
        for i in self.male_group:
            p = self.people[i]
            if p.has_partner:
                if random.random() < PROB_RUPTURA:
                    has_partner = p.has_partner
                    p.has_partner = None
                    has_partner.has_partner = None

                    p.desires_partner = False
                    has_partner.desires_partner = False
                    p.time_left_single  = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(p.age))
                    has_partner.time_left_single  = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(has_partner.age))

    def handle_pregnancies(self, time):
        """Initiate pregnancies for partnered women and add to gestations list."""
        # 7. embarazos

        for i in self.female_group:
            p = self.people[i]
            if p.is_able_to_reproduce():

                prob = prob_by_age(p.age, PROB_EMBARAZO)

                if random.random() < prob:
                    num_bebes = RandomSampler.sample(PROB_BEBES)
                    
                    gest_time = random.uniform(7, 10) / 12   # any value between 7.0 and 10.0
                    for _ in range(num_bebes):
                        self.add_person (self.create_baby(gest_time))  # Agregar bebé a gestación

                    p.children_count += num_bebes
                    p.has_partner.children_count += num_bebes
                    p.time_left_in_pregnancy = gest_time  # meses de embarazo, convertido a años
                    

# EJECUCION
if __name__ == "__main__":

    sim = Simulador(H=100, M=100)
    historia = sim.run(100)

    print("Población final:", historia[-1])
    

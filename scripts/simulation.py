"""Main engine for simulating population dynamics over time."""

import random  # Random number utilities for stochastic events.
from typing import List, Tuple, Callable  # Type hints for schedules and callables.
from scripts.person import Person  # Population entity model.
from scripts.sampler import RandomSampler  # Random distribution sampling helpers.
from scripts.table import (  # Probability tables and lookup helper.
    PROB_MUERTE_H,
    PROB_MUERTE_M,
    PROB_EMBARAZO,
    PROB_QUERER_PAREJA,
    PROB_FORMAR_PAREJA,
    PROB_RUPTURA,
    MEDIA_SOLO,
    PROB_BEBES,
    PROB_DESEO,
    prob_by_age,
)


# SIMULATOR ----------------------------------
class Simulador:
    """Main simulation engine for population dynamics."""

    def __init__(self, H, M):
        """Initialize simulator with H males and M females."""
        # Initialize data structures for tracking individuals
        self.people: dict[int, Person] = {}
        self.male_group: set[int] = set()
        self.female_group: set[int] = set()
        self.gestation: set[int] = set()
        self.next_id = 0

        # Create initial population of males and females
        for _ in range(H):
            self.add_person(self.create_person('H'))

        for _ in range(M):
            self.add_person(self.create_person('M'))

    @property
    def population(self):
        """Return list of all living persons in the simulation."""
        return [self.people[i] for i in self.male_group.union(self.female_group)]

    # MANAGE PEOPLE -------------------------------------------------------------------
    def add_person(self, persona):
        """Add a person to the simulation and track by sex."""
        # Store person and classify by age/sex
        self.people[persona.id] = persona
        
        if persona.age < 0:
            self.gestation.add(persona.id)
        elif persona.sex == 'H':
            self.male_group.add(persona.id)
        else:
            self.female_group.add(persona.id)

    def create_person(self, sex):
        """Create a new person with random age and desired number of children."""
        # Generate new person with random age and fertility desires
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
        # Randomly assign sex (50/50 probability)
        sex = 'H' if random.random() < 0.5 else 'M' 

        # Create baby with negative age to track gestation period
        bebe = Person(
            id=self.next_id,
            age= -gest_time,  # The baby starts with a negative age equal to gestation time.
            sex=sex,
            child_desire_count=RandomSampler.sample(PROB_DESEO)
        )
        self.next_id += 1
        return bebe

    # BUILD SCHEDULE -------------------------------------------------------------------
    def build_events_by_type(
        self,
        funcion: Callable,
        lam: float,
        anos_simulacion: float
    ) -> List[Tuple[float, Callable]]:

        """Build a timeline of repeated events for a single handler."""
        # Generate random event times throughout the simulation period
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
        """Build the full sorted event schedule for the simulation."""
        # Define event types with their frequency rates
        tipos_eventos = [
            (self.handle_deaths, 0.05),
            (self.partner_desire, 1.0),
            (self.handle_breakups, 0.2),
            (self.match_couples, 0.5),
            (self.handle_pregnancies, 0.1),
        ]

        eventos_globales: List[Tuple[float, Callable]] = []

        # Generate event timeline for each event type
        for funcion, lam in tipos_eventos:
            agenda = self.build_events_by_type(
                funcion=funcion,
                lam=lam,
                anos_simulacion=anos_simulacion
            )
            eventos_globales.extend(agenda)

        # Merge and sort all events by time
        eventos_globales.sort(key=lambda x: x[0])

        return eventos_globales

    def run(self, anos=100):
        """Run the simulation and return the population history as list of (time, population)."""
        
        # Initialize history tracker and event schedule
        history: List[Tuple[float, int]] = [(0.0, len(self.population))]
        
        last_time = 0.0
        agenda_eventos = self.build_event_schedule(anos)

        # Process each event in chronological order
        for t, funcion in agenda_eventos:
            diff = t - last_time
            
            # Age people and process pregnancies between events
            self.age_people(diff)
            self.update_gestations(diff)
            
            # Execute the current event handler
            funcion(diff)
            
            # Record population size at this moment
            history.append((t, len(self.population)))
            last_time = t

        return history

    # UPDATES -------------------------------------------------------------------
    def age_people(self, time):
        """Age all living persons by one month."""
        # Advance age for all living individuals
        for p in self.population:
            p.age_up (time)

    def update_gestations(self, time):
        """Process ongoing gestations and add born babies to the population."""
        # Age all fetuses and handle births
        for item in self.gestation.copy():  # Copy the set to avoid mutating it during iteration
            bebe = self.people[item]
            bebe.age_up (time)

            # Check if baby has completed gestation period
            if bebe.age >= 0:
                # Add newborn to population groups
                self.add_person (bebe)
                self.gestation.discard(bebe.id)  # Remove from gestation tracking

    # EVENT HANDLERS -------------------------------------------------------------------
    def handle_deaths(self, time):
        """Apply mortality and handle relationship dissolution from deaths."""
        # Apply mortality based on age and sex
        for p in self.population:
            # Select appropriate mortality table by sex
            tabla = PROB_MUERTE_H if p.sex == 'H' else PROB_MUERTE_M
            if random.random() < prob_by_age(p.age, tabla):
                # Mark person as deceased
                p.is_alive = False

                # If deceased had a partner, end their relationship
                if p.has_partner:
                    has_partner = p.has_partner
                    has_partner.has_partner = None
                    # Set recovery period for surviving partner
                    has_partner.time_left_single  = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(has_partner.age))
                    p.has_partner = None
                
                # Remove from sex-specific groups
                if p.sex == 'H':
                    self.male_group.discard(p.id)
                else:
                    self.female_group.discard(p.id)

    def partner_desire(self, time):
        """Update desire for partnership based on age and availability."""
        # Update desires for single individuals based on age-specific probabilities
        for p in self.population:
            if p.is_single():
                p.desires_partner = random.random() < prob_by_age(p.age, PROB_QUERER_PAREJA)

    def match_couples(self, time):
        """Match available individuals who desire partnerships based on age compatibility."""
        # Filter eligible single individuals seeking partners
        male_group = [self.people[i] for i in self.male_group if self.people[i].is_single() and self.people[i].desires_partner]
        female_group = [self.people[i] for i in self.female_group if self.people[i].is_single() and self.people[i].desires_partner]

        # Randomize order to vary matching outcomes
        random.shuffle(male_group)
        random.shuffle(female_group)

        # Attempt to form couples based on age compatibility
        for h in male_group:
            # Each male tries multiple candidates instead of only the first one
            for m in female_group:
                if not m.is_single():
                    continue

                # Compute age difference and matching probability
                diff = abs(h.age - m.age)
                p = prob_by_age(diff, PROB_FORMAR_PAREJA)

                # Form couple if random check passes
                if random.random() < p:
                    h.has_partner = m
                    m.has_partner = h
                    break  # Stop once the couple is formed

    def handle_breakups(self, time):
        """Randomly dissolve some partnerships and set solitude recovery time."""
        # Randomly end some active relationships
        for i in self.male_group:
            p = self.people[i]
            if p.has_partner:
                # Check if relationship breaks based on probability
                if random.random() < PROB_RUPTURA:
                    has_partner = p.has_partner
                    # Sever relationship on both sides
                    p.has_partner = None
                    has_partner.has_partner = None

                    # Reset partnership desires and set solitude recovery period
                    p.desires_partner = False
                    has_partner.desires_partner = False
                    p.time_left_single  = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(p.age))
                    has_partner.time_left_single  = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(has_partner.age))

    def handle_pregnancies(self, time):
        """Initiate pregnancies for partnered women and add to gestations list."""
        # Process pregnancy events for eligible women
        for i in self.female_group:
            p = self.people[i]
            if p.is_able_to_reproduce():
                # Check pregnancy probability based on age
                prob = prob_by_age(p.age, PROB_EMBARAZO)

                if random.random() < prob:
                    # Determine number of babies (singleton, twins, etc.)
                    num_bebes = RandomSampler.sample(PROB_BEBES)
                    
                    # Generate random gestation period (7-10 months converted to years)
                    gest_time = random.uniform(7, 10) / 12
                    # Create and add each baby to gestation tracking
                    for _ in range(num_bebes):
                        self.add_person (self.create_baby(gest_time))

                    # Update child counts for both parents
                    p.children_count += num_bebes
                    p.has_partner.children_count += num_bebes
                    # Set pregnancy recovery period
                    p.time_left_in_pregnancy = gest_time
                    


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


def prob_por_edad(edad, tabla):
    for a, b, p in tabla:
        if a <= edad < b:
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
    def lambda_solo(edad):
        """Calculate the rate parameter for exponential distribution of solitude time."""
        media = prob_por_edad(edad, MEDIA_SOLO)
        return 1/media if media > 0 else 0

    @staticmethod
    def sample_exponencial(lmbda):
        """Sample from exponential distribution and convert months to years."""
        if lmbda == 0:
            return 0
        return random.expovariate(lmbda)/12  # Convertir de meses a años
    
    @staticmethod
    def salto_tiempo(lam=1.5, min_dias=1, max_anos=5):
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
class Persona:
    """Represents an individual in the population with demographic and social attributes."""
    id: int
    edad: float  # años
    sexo: str  # 'H' o 'M'
    pareja: Optional["Persona"] = None
    hijos: int = 0
    deseo_hijos: int = 1
    quiere_pareja: bool = False
    tiempo_solo_restante: float = 0.0  # meses
    embarazo_restante: float = 0.0  # meses
    viva: bool = True

    def envejecer(self, time):
        """Age the person by one month."""
        self.edad += time
        
        if self.embarazo_restante > 0:
            self.embarazo_restante -= time
            if self.embarazo_restante < 0:
                self.embarazo_restante = 0
                       
        if self.tiempo_solo_restante > 0:
            self.tiempo_solo_restante -= time
        elif self.tiempo_solo_restante < 0:
            self.tiempo_solo_restante = 0
            
    def esta_disponible(self):
        """Check if person is alive, single, and ready for a new relationship."""
        return (
            self.viva and
            self.pareja is None and
            self.tiempo_solo_restante <= 0
        )

    def puede_tener_hijos(self):
        """Check if person can have children based on sex, status, and desires."""
        if not self.viva or self.sexo != "M":
            return False
        if self.pareja is None:
            return False
        if self.embarazo_restante > 0:
            return False
        limite = min(self.deseo_hijos, self.pareja.deseo_hijos)
        return self.hijos < limite


# SIMULADOR
class Simulador:
    """Main simulation engine for population dynamics."""

    def __init__(self, H, M):
        """Initialize simulator with H males and M females."""
        self.personas: dict[int, Persona] = {}
        self.hombres: set[int] = set()
        self.mujeres: set[int] = set()
        self.gestation: set[int] = set()
        self.next_id = 0

        # inicialización
        for _ in range(H):
            self.agregar_persona(self.crear_persona('H'))

        for _ in range(M):
            self.agregar_persona(self.crear_persona('M'))

    @property
    def poblacion(self):
        """Return list of all living persons in the simulation."""
        return [self.personas[i] for i in self.hombres.union(self.mujeres)]

    # GESTIONAR PERSONAS ------------------------
    def agregar_persona(self, persona):
        """Add a person to the simulation and track by sex."""
        self.personas[persona.id] = persona
        
        if persona.edad < 0:
            self.gestation.add(persona.id)
        elif persona.sexo == 'H':
            self.hombres.add(persona.id)
        else:
            self.mujeres.add(persona.id)

    def crear_persona(self, sexo):
        """Create a new person with random age and desired number of children."""
        p = Persona(
            id=self.next_id,
            edad=random.uniform(0,100),
            sexo=sexo,
            deseo_hijos=RandomSampler.sample(PROB_DESEO)
        )
        self.next_id += 1
        return p

    def crear_bebe(self, gest_time):
        """Create a new baby with random sex and gestation time."""
        # Sexo aleatorio: 0 = hombre, 1 = mujer
        sexo = 'H' if random.random() < 0.5 else 'M' 

        bebe = Persona(
            id=self.next_id,
            edad= -gest_time,  # siempre nace con edad: - gest_time
            sexo=sexo,
            deseo_hijos=RandomSampler.sample(PROB_DESEO)
        )
        self.next_id += 1
        return bebe

    # CREAR AGENDA -------------------------------
    def _generar_eventos_tipo(
        self,
        funcion: Callable,
        lam: float,
        anos_simulacion: float
    ) -> List[Tuple[float, Callable]]:

        t = 0.0
        agenda = []

        while t < anos_simulacion:
            dt = RandomSampler.salto_tiempo(lam=lam)
            t += dt

            if t > anos_simulacion:
                break

            agenda.append((t, funcion))

        return agenda

    def gestar_agenda_eventos(self, anos_simulacion: float):

        tipos_eventos = [
            (self.aplicar_muertes, 0.05),
            (self.actualizar_deseo_pareja, 1.0),
            (self.aplicar_rupturas, 0.2),
            (self.formar_parejas, 0.5),
            (self.procesar_embarazos, 0.1),
        ]

        eventos_globales: List[Tuple[float, Callable]] = []

        for funcion, lam in tipos_eventos:
            agenda = self._generar_eventos_tipo(
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
        Ejecuta la simulación y devuelve historia de población viva.
        """

        historia = []
        last_time=0
        agenda_eventos = self.gestar_agenda_eventos(anos)

        for t, funcion in agenda_eventos:
            # Ejecutar evento
            diff = t - last_time
            self.envejecer_poblacion(diff)
            self.procesar_gestaciones(diff)
            funcion(diff)
            historia.append(len(self.poblacion))
            last_time = t

        return historia

    # ACTUALIZAR ----------------------------------
    def envejecer_poblacion(self, time):
        """Age all living persons by one month."""
        # 1. envejecer
        for p in self.poblacion:
            p.envejecer(time)

    def procesar_gestaciones(self, time):
        """Process ongoing gestations and add born babies to the population."""
        # 6.5. Procesar gestaciones: reducir el tiempo restante y crear personas cuando llegue a 0
        
        for item in self.gestation.copy():  # Copia para evitar modificar el set durante la iteración
            bebe = self.personas[item]
            bebe.envejecer(time)

            if bebe.edad >= 0:
                # Bebé completó gestación, agregarlo a la población
                self.agregar_persona(bebe)
                self.gestation.discard(bebe.id)  # Quitar de gestación

    # EVENTOS -------------------------------------
    def aplicar_muertes(self, time):
        """Apply mortality and handle relationship dissolution from deaths."""
        # 2. muerte

        for p in self.poblacion:

            tabla = PROB_MUERTE_H if p.sexo == 'H' else PROB_MUERTE_M
            if random.random() < prob_por_edad(p.edad, tabla):
                p.viva = False

                if p.pareja:
                    pareja = p.pareja
                    pareja.pareja = None
                    pareja.tiempo_solo_restante = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(pareja.edad))
                    p.pareja = None
                
                if p.sexo == 'H':
                    self.hombres.discard(p.id)
                else:
                    self.mujeres.discard(p.id)

    def actualizar_deseo_pareja(self, time):
        """Update desire for partnership based on age and availability."""
        # 4. deseo de pareja
        for p in self.poblacion:
            if p.esta_disponible():
                p.quiere_pareja = random.random() < prob_por_edad(p.edad, PROB_QUERER_PAREJA)

    def formar_parejas(self, time):
        """Match available individuals who desire partnerships based on age compatibility."""
        # Filtrar personas disponibles y con deseo de pareja
        hombres = [self.personas[i] for i in self.hombres if self.personas[i].esta_disponible() and self.personas[i].quiere_pareja]
        mujeres = [self.personas[i] for i in self.mujeres if self.personas[i].esta_disponible() and self.personas[i].quiere_pareja]

        random.shuffle(hombres)
        random.shuffle(mujeres)

        for h in hombres:
            # Cada hombre intenta con varias mujeres, no solo con la mejor
            for m in mujeres:
                if not m.esta_disponible():
                    continue

                diff = abs(h.edad - m.edad)
                p = prob_por_edad(diff, PROB_FORMAR_PAREJA)

                # Aumentar probabilidad de éxito multiplicando por un factor
                if random.random() < p:  # factor > 1 aumenta colisiones
                    h.pareja = m
                    m.pareja = h
                    break  # salir del bucle, ya emparejado

    def aplicar_rupturas(self, time):
        """Randomly dissolve some partnerships and set solitude recovery time."""
        # 6. rupturas
        for i in self.hombres:
            p = self.personas[i]
            if p.pareja:
                if random.random() < PROB_RUPTURA:
                    pareja = p.pareja
                    p.pareja = None
                    pareja.pareja = None

                    p.quiere_pareja = False
                    pareja.quiere_pareja = False
                    p.tiempo_solo_restante = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(p.edad))
                    pareja.tiempo_solo_restante = RandomSampler.sample_exponencial(RandomSampler.lambda_solo(pareja.edad))

    def procesar_embarazos(self, time):
        """Initiate pregnancies for partnered women and add to gestations list."""
        # 7. embarazos

        for i in self.mujeres:
            p = self.personas[i]
            if p.puede_tener_hijos():

                prob = prob_por_edad(p.edad, PROB_EMBARAZO)

                if random.random() < prob:
                    num_bebes = RandomSampler.sample(PROB_BEBES)
                    
                    gest_time = random.uniform(7, 10) / 12   # any value between 7.0 and 10.0
                    for _ in range(num_bebes):
                        self.agregar_persona(self.crear_bebe(gest_time))  # Agregar bebé a gestación

                    p.hijos += num_bebes
                    p.pareja.hijos += num_bebes
                    p.embarazo_restante = gest_time  # meses de embarazo, convertido a años
                    

# EJECUCION
if __name__ == "__main__":

    sim = Simulador(H=100, M=100)
    historia = sim.run(120)

    #print("Población final:", historia[-1])
    print(historia[-1])
    

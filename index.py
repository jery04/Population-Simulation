import random
import math
from dataclasses import dataclass
from typing import Optional, List

# =========================
# MODELO
# =========================

@dataclass
class Persona:
    id: int
    edad: float  # años
    sexo: str  # 'H' o 'M'
    pareja: Optional["Persona"] = None
    hijos: int = 0
    deseo_hijos: int = 1
    quiere_pareja: bool = False
    tiempo_solo_restante: float = 0.0  # meses
    viva: bool = True

    def envejecer(self):
        self.edad += 1/12

    def esta_disponible(self):
        return (
            self.viva and
            self.pareja is None and
            self.tiempo_solo_restante <= 0
        )

    def puede_tener_hijos(self):
        if not self.viva or self.sexo != "M":
            return False
        if self.pareja is None:
            return False
        limite = min(self.deseo_hijos, self.pareja.deseo_hijos)
        return self.hijos < limite


# =========================
# TABLAS
# =========================

def prob_por_edad(edad, tabla):
    for a, b, p in tabla:
        if a <= edad < b:
            return p
    return 0.0


PROB_MUERTE_H = [(0,12,0.25),(12,45,0.1),(45,76,0.3),(76,126,0.7)]
PROB_MUERTE_M = [(0,12,0.25),(12,45,0.15),(45,76,0.35),(76,126,0.65)]

PROB_EMBARAZO = [(12,15,0.2),(15,21,0.45),(21,35,0.8),
                 (35,45,0.4),(45,60,0.2),(60,126,0.05)]

PROB_QUERER_PAREJA = [(12,15,0.6),(15,21,0.65),(21,35,0.8),
                      (35,45,0.6),(45,60,0.5),(60,126,0.2)]

PROB_FORMAR_PAREJA = [(0,5,0.45),(5,10,0.4),(10,15,0.35),
                      (15,20,0.25),(20,999,0.15)]

PROB_RUPTURA = 0.2

MEDIA_SOLO = [(12,15,3),(15,21,6),(21,35,6),
              (35,45,12),(45,60,24),(60,126,48)]

# Normalizar para que sume exactamente 1.0
_bebes_raw = {1:0.7,2:0.18,3:0.08,4:0.04,5:0.02}
_bebes_total = sum(_bebes_raw.values())
PROB_BEBES = {k: v/_bebes_total for k,v in _bebes_raw.items()}

# normalizar deseo hijos
DESEO_RAW = {1:0.6,2:0.75,3:0.35,4:0.2,5:0.1,6:0.05}
total = sum(DESEO_RAW.values())
PROB_DESEO = {k:v/total for k,v in DESEO_RAW.items()}


# =========================
# SAMPLING
# =========================

def sample(dic):
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


def lambda_solo(edad):
    media = prob_por_edad(edad, MEDIA_SOLO)
    return 1/media if media > 0 else 0

def sample_exponencial(lmbda):
    if lmbda == 0:
        return 0
    return random.expovariate(lmbda)


# =========================
# SIMULADOR
# =========================

class Simulador:

    def __init__(self, H, M):
        self.poblacion: List[Persona] = []
        self.next_id = 0

        # inicialización
        for _ in range(H):
            self.poblacion.append(self.crear_persona('H'))

        for _ in range(M):
            self.poblacion.append(self.crear_persona('M'))

    def crear_persona(self, sexo):
        p = Persona(
            id=self.next_id,
            edad=random.uniform(0,100),
            sexo=sexo,
            deseo_hijos=sample(PROB_DESEO)
        )
        self.next_id += 1
        return p

    # =====================
    # PASO DE SIMULACION
    # =====================

    def step(self):

        # 1. envejecer
        for p in self.poblacion:
            if p.viva:
                p.envejecer()

        # 2. muerte
        for p in self.poblacion:
            if not p.viva:
                continue

            tabla = PROB_MUERTE_H if p.sexo == 'H' else PROB_MUERTE_M
            if random.random() < prob_por_edad(p.edad, tabla):
                p.viva = False

                if p.pareja:
                    pareja = p.pareja
                    pareja.pareja = None
                    pareja.tiempo_solo_restante = sample_exponencial(lambda_solo(pareja.edad))
                    p.pareja = None

        # 3. reducir tiempo solo
        for p in self.poblacion:
            if p.tiempo_solo_restante > 0:
                p.tiempo_solo_restante -= 1

        # 4. deseo de pareja
        for p in self.poblacion:
            if p.viva:
                p.quiere_pareja = random.random() < prob_por_edad(p.edad, PROB_QUERER_PAREJA)

        # 5. formar parejas
        solteros = [p for p in self.poblacion if p.esta_disponible()]
        random.shuffle(solteros)

        for i in range(0, len(solteros)-1, 2):
            a = solteros[i]
            b = solteros[i+1]

            if a.sexo == b.sexo:
                continue

            if not (a.quiere_pareja and b.quiere_pareja):
                continue

            diff = abs(a.edad - b.edad)
            p = prob_por_edad(diff, PROB_FORMAR_PAREJA)

            if random.random() < p:
                a.pareja = b
                b.pareja = a

        # 6. rupturas
        for p in self.poblacion:
            if p.viva and p.pareja:
                if random.random() < PROB_RUPTURA:
                    pareja = p.pareja
                    p.pareja = None
                    pareja.pareja = None

                    p.tiempo_solo_restante = sample_exponencial(lambda_solo(p.edad))
                    pareja.tiempo_solo_restante = sample_exponencial(lambda_solo(pareja.edad))

        # 7. embarazos
        nuevos = []

        for p in self.poblacion:
            if p.puede_tener_hijos():

                prob = prob_por_edad(p.edad, PROB_EMBARAZO)

                if random.random() < prob:
                    num_bebes = sample(PROB_BEBES)

                    for _ in range(num_bebes):
                        sexo = 'H' if random.random() < 0.5 else 'M'
                        bebe = self.crear_persona(sexo)
                        bebe.edad = 0
                        nuevos.append(bebe)

                    p.hijos += num_bebes
                    p.pareja.hijos += num_bebes

        self.poblacion.extend(nuevos)

    # =====================
    # EJECUTAR
    # =====================

    def run(self, meses=1200):
        historia = []

        for _ in range(meses):
            self.step()
            vivos = sum(1 for p in self.poblacion if p.viva)
            historia.append(vivos)

        return historia


# =========================
# EJECUCION
# =========================

if __name__ == "__main__":

    sim = Simulador(H=100, M=100)

    historia = sim.run(1200)

    print("Población final:", historia[-1])
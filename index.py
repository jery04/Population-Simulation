import random
from dataclasses import dataclass
from typing import Optional, List, Tuple

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
    embarazo_restante: float = 0.0  # meses
    viva: bool = True

    def envejecer(self):
        self.edad += 1/12
        if self.embarazo_restante > 0:
            self.embarazo_restante -= 1/12
            if self.embarazo_restante < 0:
                self.embarazo_restante = 0

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
        if self.embarazo_restante > 0:
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


PROB_MUERTE_H = [(0,12,0.25/12),(12,45,0.1/12),(45,76,0.3/12),(76,126,0.7/12)]
PROB_MUERTE_M = [(0,12,0.25/12),(12,45,0.15/12),(45,76,0.35/12),(76,126,0.65/12)]

PROB_EMBARAZO = [(12,15,0.2),(15,21,0.45),(21,35,0.8), (35,45,0.4),(45,60,0.2),(60,126,0.05)]

PROB_QUERER_PAREJA = [(12,15,0.6),(15,21,0.65),(21,35,0.8),(35,45,0.6),(45,60,0.5),(60,126,0.2)]

PROB_FORMAR_PAREJA = [(0,5,0.45),(5,10,0.4),(10,15,0.35),(15,20,0.25),(20,999,0.15)]

PROB_RUPTURA = 0.2

MEDIA_SOLO = [(12,15,3),(15,21,6),(21,35,6),(35,45,12),(45,60,24),(60,126,48)]

# Normalizar para que sume exactamente 1.0
_bebes_raw = {1:0.7,2:0.18,3:0.08,4:0.04,5:0.02}
_bebes_total = sum(_bebes_raw.values())
PROB_BEBES = {k: v/_bebes_total for k,v in _bebes_raw.items()}

# normalizar deseo hijos
DESEO_RAW = {1:0.6,2:0.75,3:0.35,4:0.2,5:0.1,6:0.016,7:0.016,8:0.016}
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
        self.hombres: List[Persona] = []
        self.mujeres: List[Persona] = []
        self.embarazos: List[Tuple[Persona, float]] = []  # (bebé, tiempo restante hasta nacer)
        self.next_id = 0

        # inicialización
        for _ in range(H):
            self.agregar_persona(self.crear_persona('H'))

        for _ in range(M):
            self.agregar_persona(self.crear_persona('M'))

    def agregar_persona(self, persona):
        if persona.sexo == 'H':
            self.hombres.append(persona)
        else:
            self.mujeres.append(persona)

    @property
    def poblacion(self):
        return self.hombres + self.mujeres

    def crear_persona(self, sexo):
        p = Persona(
            id=self.next_id,
            edad=random.uniform(0,100),
            sexo=sexo,
            deseo_hijos=sample(PROB_DESEO)
        )
        self.next_id += 1
        return p

    def crear_bebe(self):
        # Sexo aleatorio: 0 = hombre, 1 = mujer
        sexo = 'H' if random.random() < 0.5 else 'M' 

        meses = random.choice([7, 8, 9, 10])
        tiempo = meses / 12

        bebe = Persona(
            id=self.next_id,
            edad=0,  # siempre nace con edad 0
            sexo=sexo,
            deseo_hijos=sample(PROB_DESEO)
        )

        self.next_id += 1
        return bebe, tiempo

    def run(self, meses=1200):
        historia = []

        for _ in range(meses):
            self.step()
            vivos = sum(1 for p in self.poblacion if p.viva)
            historia.append(vivos)

        return historia

    def step(self):

        self.procesar_gestaciones()      # 1. nacen bebés (antes de todo)
        self.envejecer_poblacion()       # 2. todos envejecen
        self.aplicar_muertes()           # 3. algunos mueren (afecta relaciones)

        self.reducir_tiempo_solo()       # 4. pasa el tiempo emocional/social
        self.actualizar_deseo_pareja()   # 5. cambia el deseo (depende de edad actual)

        self.aplicar_rupturas()          # 6. relaciones existentes pueden romperse
        self.formar_parejas()            # 7. nuevos emparejamientos

        self.procesar_embarazos()        # 8. embarazos (requiere pareja estable)

    def envejecer_poblacion(self):

        # 1. envejecer
        for p in self.poblacion:
            if p.viva:
                p.envejecer()

    def aplicar_muertes(self):

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

    def reducir_tiempo_solo(self):

        # 3. reducir tiempo solo
        for p in self.poblacion:
            if p.tiempo_solo_restante > 0:
                p.tiempo_solo_restante -= 1/12
            elif p.tiempo_solo_restante < 0:
                p.tiempo_solo_restante = 0

    def actualizar_deseo_pareja(self):

        # 4. deseo de pareja
        for p in self.poblacion:
            if p.viva:
                p.quiere_pareja = random.random() < prob_por_edad(p.edad, PROB_QUERER_PAREJA)

    def formar_parejas(self):
        # Filtrar personas disponibles y con deseo de pareja
        hombres = [p for p in self.hombres if p.esta_disponible() and p.quiere_pareja]
        mujeres = [p for p in self.mujeres if p.esta_disponible() and p.quiere_pareja]

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

    def aplicar_rupturas(self):

        # 6. rupturas
        for p in self.hombres:
            if p.viva and p.pareja:
                if random.random() < PROB_RUPTURA:
                    pareja = p.pareja
                    p.pareja = None
                    pareja.pareja = None

                    p.tiempo_solo_restante = sample_exponencial(lambda_solo(p.edad))
                    pareja.tiempo_solo_restante = sample_exponencial(lambda_solo(pareja.edad))

    def procesar_gestaciones(self):
        # 6.5. Procesar gestaciones: reducir el tiempo restante y crear personas cuando llegue a 0
        embarazos_restantes = []
        
        for bebe, tiempo_restante in self.embarazos:
            bebe.envejecer()

            if tiempo_restante - bebe.edad <= 0:
                # Bebé completó gestación, agregarlo a la población
                self.agregar_persona(bebe)
            else:
                # Aún en gestación
                embarazos_restantes.append((bebe, tiempo_restante))
        
        self.embarazos = embarazos_restantes

    def procesar_embarazos(self):
        # 7. embarazos

        for p in self.mujeres:
            if p.puede_tener_hijos():

                prob = prob_por_edad(p.edad, PROB_EMBARAZO)

                if random.random() < prob:
                    num_bebes = sample(PROB_BEBES)

                    for _ in range(num_bebes):
                        bebe = self.crear_bebe()
                        self.embarazos.append(bebe)  # Agregar bebé a gestación con su tiempo de nacimiento

                    p.hijos += num_bebes
                    p.pareja.hijos += num_bebes


# =========================
# EJECUCION
# =========================

if __name__ == "__main__":

    sim = Simulador(H=100, M=100)
    historia = sim.run(12)

    #print("Población final:", historia[-1])
    print(historia[:12])
    

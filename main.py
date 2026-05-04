import random
from typing import List, Tuple, Callable

from index import RandomSampler

DIAS_EN_ANO = 365


# --------------------------------------------------
# 🔹 SALTO DE TIEMPO
# --------------------------------------------------



# --------------------------------------------------
# 🔹 SIMULADOR
# --------------------------------------------------
class Simulador:

    # -------------------------
    # EVENTOS (ejemplo)
    # -------------------------
    def aplicar_muertes(self):
        print("Evento: muertes")

    def actualizar_deseo_pareja(self):
        print("Evento: deseo")

    def aplicar_rupturas(self):
        print("Evento: rupturas")

    def formar_parejas(self):
        print("Evento: formar parejas")

    def procesar_embarazos(self):
        print("Evento: embarazos")

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

        # 🔥 Merge ordenado
        eventos_globales.sort(key=lambda x: x[0])

        return eventos_globales


# --------------------------------------------------
# 🔹 USO
# --------------------------------------------------
if __name__ == "__main__":

    sim = Simulador()
    agenda = sim.gestar_agenda_eventos(50)

    # Mostrar
    for t, func in agenda:
        print(f"{t:.3f} -> {func.__name__}")

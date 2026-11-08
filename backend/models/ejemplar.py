"""Entidad de dominio Ejemplar."""

from dataclasses import dataclass

from .excepciones import ReglaNegocio, validar_texto_obligatorio


@dataclass
class Ejemplar:
    """Copia física de un material asociada a una sede de pertenencia."""

    codigo: str
    libro_id: int
    sede_pertenencia_id: int
    sede_actual_id: int
    estado: str = "DISPONIBLE"
    condicion: str = "BUENO"
    id: int | None = None

    ESTADOS_VALIDOS = {
        "DISPONIBLE",
        "APARTADO",
        "RESERVADO",
        "PRESTADO",
        "EN_TRANSITO",
        "POR_RETORNAR",
        "EN_REVISION",
        "BAJA",
    }
    CONDICIONES_VALIDAS = {"BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO"}

    def __post_init__(self) -> None:
        self.codigo = validar_texto_obligatorio(self.codigo, "Código")
        self.condicion = validar_texto_obligatorio(self.condicion, "Condición").upper()
        if self.estado not in self.ESTADOS_VALIDOS:
            raise ReglaNegocio(f"Estado de ejemplar inválido: {self.estado}")
        if self.condicion not in self.CONDICIONES_VALIDAS:
            raise ReglaNegocio(f"Condición de ejemplar inválida: {self.condicion}")

    @property
    def esta_disponible(self) -> bool:
        return self.estado == "DISPONIBLE"

    def asegurar_en_sede_origen(self, sede_origen_id: int) -> None:
        if self.sede_pertenencia_id != sede_origen_id or self.sede_actual_id != sede_origen_id:
            raise ReglaNegocio("El ejemplar no pertenece o no se encuentra en la sede de origen")

    def apartar(self) -> None:
        if self.estado not in {"DISPONIBLE", "RESERVADO", "EN_TRANSITO"}:
            raise ReglaNegocio("El ejemplar no está disponible")
        self.estado = "APARTADO"

    def reservar(self) -> None:
        if self.estado != "DISPONIBLE":
            raise ReglaNegocio("Solo se puede reservar un ejemplar disponible")
        self.estado = "RESERVADO"

    def liberar(self) -> None:
        self.estado = "DISPONIBLE"

    def prestar(self) -> None:
        self.estado = "PRESTADO"

    def despachar(self) -> None:
        self.estado = "EN_TRANSITO"

    def marcar_por_retornar(self) -> None:
        self.estado = "POR_RETORNAR"

    def enviar_a_revision(self) -> None:
        self.estado = "EN_REVISION"

    def dar_de_baja(self) -> None:
        self.estado = "BAJA"

    def recibir_en(self, sede_destino_id: int, estado_final: str) -> None:
        if estado_final not in self.ESTADOS_VALIDOS:
            raise ReglaNegocio(f"Estado de ejemplar inválido: {estado_final}")
        self.sede_actual_id = sede_destino_id
        self.estado = estado_final

    def cerrar_revision(self, apto: bool) -> None:
        if self.estado != "EN_REVISION":
            raise ReglaNegocio("El ejemplar no está en revisión")
        self.estado = "DISPONIBLE" if apto else "BAJA"

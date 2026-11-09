"""Entidad de dominio Prestamo y sus subtipos concretos."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .excepciones import ReglaNegocio, validar_texto_obligatorio


@dataclass
class Prestamo:
    """Entidad base abstracta de solicitud y préstamo de ejemplar."""

    socio_id: int
    ejemplar_id: int
    sede_origen_id: int
    sede_destino_id: int
    estado: str = "SOLICITADO"
    plazo_dias: int = 14
    solicitado_en: str | None = None
    entregado_en: str | None = None
    vence_en: str | None = None
    devuelto_en: str | None = None
    condicion_devolucion: str | None = None
    multa_centavos: int = 0
    id: int | None = None

    CONDICIONES_VALIDAS = {"BUENO", "DANADO", "DESTRUIDO", "EXTRAVIADO"}

    def __post_init__(self) -> None:
        if self.plazo_dias is None or int(self.plazo_dias) <= 0:
            raise ReglaNegocio("La duración del préstamo debe ser mayor a cero días")
        self.plazo_dias = int(self.plazo_dias)

    @property
    def tipo(self) -> str:
        raise NotImplementedError

    @property
    def requiere_remito(self) -> bool:
        return self.tipo == "INTERBIBLIOTECARIO"

    @property
    def es_interbibliotecario(self) -> bool:
        return self.tipo == "INTERBIBLIOTECARIO"

    @property
    def estado_requerido_entrega(self) -> str:
        return "LISTO" if self.es_interbibliotecario else "SOLICITADO"

    def marcar_en_transito(self) -> None:
        self.estado = "EN_TRANSITO"

    def marcar_listo(self) -> None:
        self.estado = "LISTO"

    def cancelar(self) -> None:
        if self.estado != "SOLICITADO":
            raise ReglaNegocio("Solo se puede cancelar un préstamo en estado SOLICITADO")
        self.estado = "CANCELADO"

    def entregar(self, ahora: datetime, fecha_minima_iso: str, plazo_dias: int | None = None) -> str:
        requerido = self.estado_requerido_entrega
        if self.estado != requerido:
            raise ReglaNegocio(f"El préstamo debe estar en estado {requerido} para entregarlo")
        if ahora < datetime.fromisoformat(fecha_minima_iso):
            raise ReglaNegocio("La entrega no puede preceder a la solicitud o recepción")
        dias = self.plazo_dias if plazo_dias is None else int(plazo_dias)
        if dias <= 0:
            raise ReglaNegocio("La duración del préstamo debe ser mayor a cero días")
        self.plazo_dias = dias
        vence = (ahora + timedelta(days=dias)).date().isoformat()
        self.estado = "ACTIVO"
        self.entregado_en = ahora.isoformat()
        self.vence_en = vence
        return vence

    def devolver(self, ahora: datetime, condicion: str, multa_diaria_centavos: int) -> tuple[int, str]:
        condicion_limpia = validar_texto_obligatorio(condicion, "Condición").upper()
        if condicion_limpia not in self.CONDICIONES_VALIDAS:
            raise ReglaNegocio("Condición de devolución inválida")
        if self.estado != "ACTIVO":
            raise ReglaNegocio("Solo se puede devolver un préstamo activo")
        if not self.entregado_en or ahora < datetime.fromisoformat(self.entregado_en):
            raise ReglaNegocio("La devolución no puede preceder a la entrega")

        atraso = max(0, (ahora.date() - date.fromisoformat(self.vence_en)).days)
        multa = atraso * multa_diaria_centavos
        self.estado = "DEVUELTO"
        self.devuelto_en = ahora.isoformat()
        self.condicion_devolucion = condicion_limpia
        self.multa_centavos = multa

        if condicion_limpia in {"DESTRUIDO", "EXTRAVIADO"}:
            estado_ejemplar = "BAJA"
        elif self.requiere_remito:
            estado_ejemplar = "POR_RETORNAR"
        else:
            estado_ejemplar = "DISPONIBLE" if condicion_limpia == "BUENO" else "EN_REVISION"
        return multa, estado_ejemplar

    def estado_ejemplar_al_recibir_retorno(self) -> str:
        return "DISPONIBLE" if self.condicion_devolucion == "BUENO" else "EN_REVISION"


@dataclass
class PrestamoLocal(Prestamo):
    """Préstamo cuyo retiro y devolución ocurren en la misma sede de pertenencia."""

    @property
    def tipo(self) -> str:
        return "LOCAL"


@dataclass
class PrestamoInterbibliotecario(Prestamo):
    """Préstamo entre distintas sedes que requiere logística de traslado por remito."""

    @property
    def tipo(self) -> str:
        return "INTERBIBLIOTECARIO"


SolicitudPrestamo = Prestamo

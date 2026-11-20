import logging
from datetime import datetime


# ==========================================
# BLOQUE 1: LOGGING Y EXCEPCIONES PERSONALIZADAS
# ==========================================

def configurar_logger(nombre_archivo: str = "software_fj.log") -> logging.Logger:
    """Configura el registrador de eventos y errores en archivo y consola."""
    logger = logging.getLogger("SoftwareFJ")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        archivo_handler = logging.FileHandler(nombre_archivo, encoding="utf-8")
        archivo_handler.setFormatter(formato)

        consola_handler = logging.StreamHandler()
        consola_handler.setFormatter(formato)

        logger.addHandler(archivo_handler)
        logger.addHandler(consola_handler)

    return logger


class ErrorSoftwareFJ(Exception):
    """Excepción base del sistema Software FJ."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL"):
        super().__init__(mensaje)
        self.codigo = codigo
        self.timestamp = datetime.now().isoformat()


class ErrorValidacionDato(ErrorSoftwareFJ):
    """Excepción lanzada cuando un dato es inválido o falta un parámetro."""

    def __init__(self, mensaje: str, campo: str | None = None):
        super().__init__(mensaje, codigo="ERR_VALIDACION")
        self.campo = campo


class ErrorDisponibilidadServicio(ErrorSoftwareFJ):
    """Excepción lanzada cuando un servicio no está disponible o la reserva falla."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_RESERVA")


class ErrorCalculoFinanciero(ErrorSoftwareFJ):
    """Excepción lanzada ante cálculos inconsistentes o erróneos."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_CALCULO")


import re
from abc import ABC, abstractmethod
from datetime import datetime


# ==========================================
# BLOQUE 2: MODELOS DE DOMINIO (POO)
# ==========================================

class EntidadBase:
    """Clase base con utilidades comunes de validación."""

    @staticmethod
    def validar_texto_no_vacio(valor: str, campo: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorValidacionDato(f"El campo '{campo}' no puede estar vacío.", campo=campo)
        return valor.strip()

    @staticmethod
    def validar_numero_positivo(valor: float, campo: str, permitir_cero: bool = False) -> float:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ErrorValidacionDato(f"El campo '{campo}' debe ser numérico.", campo=campo)
        if permitir_cero:
            if valor < 0:
                raise ErrorValidacionDato(f"El campo '{campo}' no puede ser negativo.", campo=campo)
        else:
            if valor <= 0:
                raise ErrorValidacionDato(f"El campo '{campo}' debe ser mayor que cero.", campo=campo)
        return float(valor)


class Cliente(EntidadBase):
    """Representa un cliente registrado en Software FJ."""

    _patron_correo = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, id_cliente: str, nombre: str, correo: str, telefono: str):
        self.id_cliente = self.validar_texto_no_vacio(id_cliente, "id_cliente")
        self.nombre = self.validar_texto_no_vacio(nombre, "nombre")
        self.correo = self._validar_correo(correo)
        self.telefono = self.validar_texto_no_vacio(telefono, "telefono")

    @classmethod
    def _validar_correo(cls, correo: str) -> str:
        correo_limpio = cls.validar_texto_no_vacio(correo, "correo")
        if not cls._patron_correo.match(correo_limpio):
            raise ErrorValidacionDato("El formato del correo electrónico no es válido.", campo="correo")
        return correo_limpio.lower()

    def to_dict(self) -> dict:
        return {
            "id_cliente": self.id_cliente,
            "nombre": self.nombre,
            "correo": self.correo,
            "telefono": self.telefono,
        }

    def __str__(self) -> str:
        return f"Cliente({self.id_cliente} - {self.nombre} | {self.correo})"


class Servicio(EntidadBase, ABC):
    """Clase abstracta que define un servicio ofertado por Software FJ."""

    def __init__(self, codigo: str, nombre: str, tarifa_base: float, disponible: bool = True):
        self.codigo = self.validar_texto_no_vacio(codigo, "codigo")
        self.nombre = self.validar_texto_no_vacio(nombre, "nombre")
        self.tarifa_base = self.validar_numero_positivo(tarifa_base, "tarifa_base")
        self.disponible = bool(disponible)

    @abstractmethod
    def calcular_costo(self, cantidad: float) -> float:
        """Calcula el costo total del servicio según la cantidad solicitada."""

    def __str__(self) -> str:
        estado = "Disponible" if self.disponible else "No disponible"
        return f"[{self.codigo}] {self.nombre} (${self.tarifa_base:,.2f}) - {estado}"


class ReservaSala(Servicio):
    """Servicio de reserva de salas por horas."""

    def __init__(self, codigo: str, nombre: str, tarifa_hora: float, capacidad: int, disponible: bool = True):
        super().__init__(codigo, nombre, tarifa_hora, disponible)
        self.capacidad = int(self.validar_numero_positivo(capacidad, "capacidad"))

    def calcular_costo(self, cantidad: float) -> float:
        horas = self.validar_numero_positivo(cantidad, "horas")
        if horas > 12:
            raise ErrorCalculoFinanciero("Una reserva de sala no puede superar las 12 horas continuas.")
        total = round(self.tarifa_base * horas, 2)
        if total <= 0:
            raise ErrorCalculoFinanciero("El costo calculado para la reserva de sala no es válido.")
        return total


class AlquilerEquipo(Servicio):
    """Servicio de alquiler de equipos tecnológicos por unidades/días."""

    def __init__(self, codigo: str, nombre: str, tarifa_unidad: float, categoria: str, disponible: bool = True):
        super().__init__(codigo, nombre, tarifa_unidad, disponible)
        self.categoria = self.validar_texto_no_vacio(categoria, "categoria")

    def calcular_costo(self, cantidad: float) -> float:
        unidades = self.validar_numero_positivo(cantidad, "unidades")
        total = round(self.tarifa_base * unidades, 2)
        if total <= 0:
            raise ErrorCalculoFinanciero("El costo calculado para el alquiler de equipo no es válido.")
        return total


class AsesoriaEspecializada(Servicio):
    """Servicio de asesoría técnica o de software por sesiones/horas."""

    def __init__(self, codigo: str, nombre: str, tarifa_sesion: float, especialidad: str, disponible: bool = True):
        super().__init__(codigo, nombre, tarifa_sesion, disponible)
        self.especialidad = self.validar_texto_no_vacio(especialidad, "especialidad")

    def calcular_costo(self, cantidad: float) -> float:
        sesiones = self.validar_numero_positivo(cantidad, "sesiones")
        descuento = 0.10 if sesiones >= 5 else 0.0
        subtotal = self.tarifa_base * sesiones
        total = round(subtotal * (1 - descuento), 2)
        if total <= 0:
            raise ErrorCalculoFinanciero("El costo calculado para la asesoría no es válido.")
        return total


class Reserva(EntidadBase):
    """Representa la reserva de un servicio por parte de un cliente."""

    ESTADOS_VALIDOS = {"CONFIRMADA", "CANCELADA", "COMPLETADA"}

    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio, cantidad: float, fecha_str: str):
        self.id_reserva = self.validar_texto_no_vacio(id_reserva, "id_reserva")
        if not isinstance(cliente, Cliente):
            raise ErrorValidacionDato("Debe asociarse un objeto Cliente válido.", campo="cliente")
        if not isinstance(servicio, Servicio):
            raise ErrorValidacionDato("Debe asociarse un objeto Servicio válido.", campo="servicio")
        if not servicio.disponible:
            raise ErrorDisponibilidadServicio(f"El servicio '{servicio.nombre}' no está disponible.")

        self.cliente = cliente
        self.servicio = servicio
        self.cantidad = self.validar_numero_positivo(cantidad, "cantidad")
        self.fecha = self._validar_fecha(fecha_str)
        self.total = self.servicio.calcular_costo(self.cantidad)
        self.estado = "CONFIRMADA"

    @staticmethod
    def _validar_fecha(fecha_str: str) -> datetime:
        texto_fecha = EntidadBase.validar_texto_no_vacio(fecha_str, "fecha")
        try:
            return datetime.strptime(texto_fecha, "%Y-%m-%d")
        except ValueError as exc:
            raise ErrorValidacionDato("La fecha debe tener el formato YYYY-MM-DD.", campo="fecha") from exc

    def cambiar_estado(self, nuevo_estado: str) -> None:
        estado_limpio = self.validar_texto_no_vacio(nuevo_estado, "estado").upper()
        if estado_limpio not in self.ESTADOS_VALIDOS:
            raise ErrorValidacionDato(f"Estado '{nuevo_estado}' no permitido.", campo="estado")
        self.estado = estado_limpio

    def __str__(self) -> str:
        return (
            f"Reserva({self.id_reserva} | {self.cliente.nombre} | "
            f"{self.servicio.nombre} x{self.cantidad} | Total: ${self.total:,.2f} | {self.estado})"
        )


# --- Prueba rápida del Bloque 2 ---
if __name__ == "__main__":
    logger = configurar_logger()
    logger.info("Probando Bloque 2 (modelos POO)...")

    cliente_prueba = Cliente("C01", "Sergio Becerra", "sergio@ejemplo.com", "3001234567")
    sala_prueba = ReservaSala("S01", "Sala de Reuniones A", 50000, capacidad=10)
    reserva_prueba = Reserva("R01", cliente_prueba, sala_prueba, 2, "2026-11-21")

    logger.info(str(cliente_prueba))
    logger.info(str(sala_prueba))
    logger.info(str(reserva_prueba))


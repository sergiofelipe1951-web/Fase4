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


# ==========================================
# BLOQUE 3: GESTOR DEL SISTEMA Y SIMULACIÓN
# ==========================================

class GestorSoftwareFJ:
    """Coordina clientes, servicios, reservas, cálculos y registro de eventos."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.clientes: dict[str, Cliente] = {}
        self.servicios: dict[str, Servicio] = {}
        self.reservas: dict[str, Reserva] = {}

    def registrar_cliente(self, cliente: Cliente) -> Cliente:
        if not isinstance(cliente, Cliente):
            raise ErrorValidacionDato("El objeto proporcionado no es un Cliente válido.", campo="cliente")
        if cliente.id_cliente in self.clientes:
            raise ErrorValidacionDato(f"Ya existe un cliente con ID '{cliente.id_cliente}'.", campo="id_cliente")
        self.clientes[cliente.id_cliente] = cliente
        self.logger.info(f"Cliente registrado: {cliente}")
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise ErrorValidacionDato("El objeto proporcionado no es un Servicio válido.", campo="servicio")
        if servicio.codigo in self.servicios:
            raise ErrorValidacionDato(f"Ya existe un servicio con código '{servicio.codigo}'.", campo="codigo")
        self.servicios[servicio.codigo] = servicio
        self.logger.info(f"Servicio registrado: {servicio}")
        return servicio

    def crear_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        codigo_servicio: str,
        cantidad: float,
        fecha_str: str,
    ) -> Reserva:
        id_limpio = EntidadBase.validar_texto_no_vacio(id_reserva, "id_reserva")
        if id_limpio in self.reservas:
            raise ErrorDisponibilidadServicio(f"Ya existe una reserva con ID '{id_limpio}'.")

        id_cli_limpio = EntidadBase.validar_texto_no_vacio(id_cliente, "id_cliente")
        if id_cli_limpio not in self.clientes:
            raise ErrorValidacionDato(f"No existe cliente con ID '{id_cli_limpio}'.", campo="id_cliente")

        cod_serv_limpio = EntidadBase.validar_texto_no_vacio(codigo_servicio, "codigo_servicio")
        if cod_serv_limpio not in self.servicios:
            raise ErrorDisponibilidadServicio(f"No existe servicio con código '{cod_serv_limpio}'.")

        cliente = self.clientes[id_cli_limpio]
        servicio = self.servicios[cod_serv_limpio]

        reserva = Reserva(
            id_reserva=id_limpio,
            cliente=cliente,
            servicio=servicio,
            cantidad=cantidad,
            fecha_str=fecha_str,
        )
        self.reservas[id_limpio] = reserva
        self.logger.info(f"Reserva creada: {reserva}")
        return reserva

    def actualizar_estado_reserva(self, id_reserva: str, nuevo_estado: str) -> Reserva:
        id_limpio = EntidadBase.validar_texto_no_vacio(id_reserva, "id_reserva")
        if id_limpio not in self.reservas:
            raise ErrorDisponibilidadServicio(f"No se encontró la reserva '{id_limpio}'.")

        reserva = self.reservas[id_limpio]
        estado_anterior = reserva.estado
        reserva.cambiar_estado(nuevo_estado)
        self.logger.info(
            f"Estado de reserva '{id_limpio}' actualizado de {estado_anterior} a {reserva.estado}."
        )
        return reserva

    def calcular_ingresos_activos(self) -> float:
        total = sum(
            r.total for r in self.reservas.values() if r.estado in {"CONFIRMADA", "COMPLETADA"}
        )
        return round(total, 2)

    def mostrar_resumen(self) -> None:
        self.logger.info("=== RESUMEN GENERAL SOFTWARE FJ ===")
        self.logger.info(f"Total clientes: {len(self.clientes)}")
        self.logger.info(f"Total servicios: {len(self.servicios)}")
        self.logger.info(f"Total reservas: {len(self.reservas)}")
        self.logger.info(f"Ingresos (CONFIRMADA/COMPLETADA): ${self.calcular_ingresos_activos():,.2f}")


def ejecutar_simulacion() -> None:
    """Ejecuta una simulación de 10 operaciones cubriendo casos válidos y errores."""
    logger = configurar_logger()
    gestor = GestorSoftwareFJ(logger)
    logger.info("Iniciando simulación de 10 operaciones en Software FJ...")

    operaciones = [
        ("Op 1 - Registrar cliente válido", lambda: gestor.registrar_cliente(
            Cliente("C01", "Sergio Becerra", "sergio@ejemplo.com", "3001234567")
        )),
        ("Op 2 - Registrar segundo cliente", lambda: gestor.registrar_cliente(
            Cliente("C02", "Paula Suarez", "paula@ejemplo.com", "3119876543")
        )),
        ("Op 3 - Cliente con correo inválido", lambda: gestor.registrar_cliente(
            Cliente("C03", "Cliente Error", "correo-no-valido", "3000000000")
        )),
        ("Op 4 - Registrar sala de reuniones", lambda: gestor.registrar_servicio(
            ReservaSala("S01", "Sala de Reuniones A", 50000, capacidad=10, disponible=True)
        )),
        ("Op 5 - Registrar equipo y asesoría", lambda: (
            gestor.registrar_servicio(AlquilerEquipo("E01", "Portátil Empresarial", 35000, "Cómputo", disponible=True)),
            gestor.registrar_servicio(AsesoriaEspecializada("A01", "Soporte de Sistemas", 80000, "Arquitectura", disponible=False)),
        )),
        ("Op 6 - Crear reserva válida de sala (2h)", lambda: gestor.crear_reserva(
            "R01", "C01", "S01", 2, "2026-11-21"
        )),
        ("Op 7 - Crear reserva válida de equipo (3 uds)", lambda: gestor.crear_reserva(
            "R02", "C02", "E01", 3, "2026-11-22"
        )),
        ("Op 8 - Intentar reservar servicio no disponible", lambda: gestor.crear_reserva(
            "R03", "C01", "A01", 1, "2026-11-23"
        )),
        ("Op 9 - Intentar reserva de sala > 12 horas", lambda: gestor.crear_reserva(
            "R04", "C01", "S01", 15, "2026-11-24"
        )),
        ("Op 10 - Completar reserva R01 y ver resumen", lambda: (
            gestor.actualizar_estado_reserva("R01", "COMPLETADA"),
            gestor.mostrar_resumen(),
        )),
    ]

    for descripcion, accion in operaciones:
        try:
            accion()
        except ErrorSoftwareFJ as err:
            logger.error(f"{descripcion} -> [{err.codigo}] {err}")
        except Exception as err:
            logger.exception(f"{descripcion} -> Error inesperado: {err}")

    logger.info("Simulación finalizada.")


if __name__ == "__main__":
    ejecutar_simulacion()


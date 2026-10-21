from abc import ABC, abstractmethod
from enum import Enum
from decimal import Decimal
from datetime import date

class RegistroNombrado(ABC):
    LIMITE = None

    def __init__(self, nombre):
        self.nombre = nombre

    @property
    def nombre(self): return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError("Nombre vacio")
        if self.LIMITE is not None and len(valor) > self.LIMITE:
            raise ValueError("Nombre demasiado largo")
        self._nombre = valor

    @abstractmethod
    def resumen(self): pass

def decimal_valido(valor, minimo=0, estricto=False, dos=False):
    d = Decimal(str(valor))
    if not d.is_finite() or d < minimo or (estricto and d == minimo):
        raise ValueError("Valor fuera de rango")
    if dos and d.as_tuple().exponent < -2:
        raise ValueError("Mas de dos decimales")
    return d

class Curso(RegistroNombrado):
    LIMITE = 200
    _siguiente_id = 1

    def __init__(self, codigo, nombre, creditos, ht, hp, hs, hv):
        super().__init__(nombre)
        self._id = Curso._siguiente_id
        Curso._siguiente_id += 1
        self.codigo = codigo
        self.creditos = creditos
        self.horas = (ht, hp, hs, hv)

    @property
    def id(self): return self._id

    @property
    def creditos(self): return self._creditos

    @creditos.setter
    def creditos(self, valor):
        self._creditos = decimal_valido(valor, 0, True, True)

    @property
    def horas(self): return self._horas

    @horas.setter
    def horas(self, valores):
        if len(valores) != 4 or any(
            type(h) is not int or not 0 <= h <= 255 for h in valores):
            raise ValueError("Horas invalidas")
        self._horas = tuple(valores)

    @property
    def horas_totales(self): return sum(self._horas)

    def resumen(self): return f"Curso {self.codigo}: {self.nombre}"

class Seccion:
    def __init__(self, codigo, codigo_curso, codigo_periodo, vacantes):
        self.codigo = codigo
        self.codigo_curso = codigo_curso
        self.codigo_periodo = codigo_periodo
        self._matriculados = 0
        self.vacantes = vacantes

    @property
    def matriculados(self): return self._matriculados

    @property
    def vacantes(self): return self._vacantes

    @vacantes.setter
    def vacantes(self, valor):
        if type(valor) is not int or valor <= 0 or valor < self._matriculados:
            raise ValueError("Vacantes invalidas")
        self._vacantes = valor

    @property
    def vacantes_disponibles(self):
        return self.vacantes - self._matriculados

    def matricular(self):
        if self.vacantes_disponibles == 0:
            raise ValueError("Seccion llena")
        self._matriculados += 1

    def retirar(self):
        if self._matriculados == 0:
            raise ValueError("Sin matriculados")
        self._matriculados -= 1

class PlanEstudio(RegistroNombrado):
    LIMITE = 36

    def __init__(self, nombre, anio, oblig, elect, extra, vigente, nuevo):
        super().__init__(nombre)
        self.anio_aprobacion = anio
        self.creditos_obligatorios = decimal_valido(oblig)
        self.creditos_electivos = decimal_valido(elect)
        self.creditos_extracurriculares = decimal_valido(extra)
        self._vigente = self._bandera(vigente)
        self._nuevo = self._bandera(nuevo)

    @staticmethod
    def _bandera(v):
        if type(v) is not int or v not in (0, 1):
            raise ValueError("Bandera invalida")
        return v

    @property
    def vigente(self): return bool(self._vigente)

    @property
    def nuevo(self): return bool(self._nuevo)

    @property
    def total_creditos(self):
        return (self.creditos_obligatorios +
                self.creditos_electivos +
                self.creditos_extracurriculares)

    def resumen(self): return f"Plan {self.nombre}, {self.anio_aprobacion}"

class EstadoPeriodo(Enum):
    PLANIFICADO = 1
    EN_CURSO = 2
    MATRICULA_CERRADA = 3
    FINALIZADO = 4

class PeriodoAcademico(RegistroNombrado):
    LIMITE = 45

    def __init__(self, nombre, numero, anio, inicio, fin,
                 inicio_m, fin_m, verano, nota_minima, estado):
        super().__init__(nombre)
        self.numero, self.anio = numero, anio
        self.cambiar_fechas(inicio, fin)
        self.cambiar_fechas_matricula(inicio_m, fin_m)
        self._verano = PlanEstudio._bandera(verano)
        self.nota_minima = nota_minima
        self.estado = estado

    @staticmethod
    def _intervalo(inicio, fin):
        if not isinstance(inicio, date) or not isinstance(fin, date) or fin < inicio:
            raise ValueError("Intervalo invalido")
        return inicio, fin

    def cambiar_fechas(self, inicio, fin):
        self._inicio, self._fin = self._intervalo(inicio, fin)

    def cambiar_fechas_matricula(self, inicio, fin):
        self._inicio_matricula, self._fin_matricula = self._intervalo(inicio, fin)

    @property
    def verano(self): return bool(self._verano)

    @property
    def nota_minima(self): return self._nota_minima

    @nota_minima.setter
    def nota_minima(self, valor):
        d = decimal_valido(valor)
        if d > 20: raise ValueError("Nota invalida")
        self._nota_minima = d

    @property
    def estado(self): return self._estado

    @estado.setter
    def estado(self, valor):
        self._estado = EstadoPeriodo(valor)

    def resumen(self): return f"Periodo {self.nombre}: {self.estado.name}"

class EscuelaProfesional(RegistroNombrado):
    def __init__(self, codigo, nombre, informacion_general,
                 perfil_egresado, codigo_director, codigo_secretario):
        super().__init__(nombre)
        self.codigo = codigo
        self.informacion_general = informacion_general
        self.perfil_egresado = perfil_egresado
        self.codigo_director = codigo_director
        self.codigo_secretario = codigo_secretario

    def resumen(self): return f"Escuela {self.codigo}: {self.nombre}"

class Persona(ABC):
    def __init__(self, dni, nombres, apellidos):
        self._dni = dni
        self._nombres = nombres
        self._apellidos = apellidos

    @property
    def nombre_completo(self):
        return f"{self._nombres} {self._apellidos}"

    @abstractmethod
    def rol(self): pass

class Estudiante(Persona):
    def __init__(self, dni, nombres, apellidos, codigo_estudiante, codigo_escuela):
        super().__init__(dni, nombres, apellidos)
        self.codigo_estudiante = codigo_estudiante
        self.codigo_escuela = codigo_escuela

    def rol(self): return "Estudiante"

class Docente(Persona):
    def __init__(self, dni, nombres, apellidos, codigo_docente):
        super().__init__(dni, nombres, apellidos)
        self.codigo_docente = codigo_docente

    def rol(self): return "Docente"

def probar(descripcion, accion):
    try:
        print(descripcion, "ACEPTADO:", accion())
    except (ValueError, AttributeError, TypeError) as e:
        print(descripcion, "RECHAZADO:", type(e).__name__)

c = Curso("IS-282", "POO", 3.5, 2, 2, 0, 0)
s = Seccion("A", "IS-282", "2026-II", 1)
p = PlanEstudio("Sistemas 2026", 2026, 100, 20, 10, 1, 0)
e = EscuelaProfesional("27", "Sistemas", "Info", "Perfil", "D01", "D02")
t = PeriodoAcademico("2026-11", 2, 2026, date(2026,8,1),
                     date(2026,12,1), date(2026,7,1), date(2026,7,15), 0, 10.5, 1)

probar("Curso valido", lambda: c.resumen())
probar("Nombre vacio", lambda: setattr(c, "nombre", ""))
probar("Nombre largo", lambda: setattr(c, "nombre", "x"*201))
probar("Credito valido", lambda: setattr(c, "creditos", 2.25))
probar("Credito cero", lambda: setattr(c, "creditos", 0))
probar("Tres decimales", lambda: setattr(c, "creditos", 1.234))
probar("Horas validas", lambda: setattr(c, "horas", (1,2,3,4)))
probar("Horas negativas", lambda: setattr(c, "horas", (-1,2,3,4)))
probar("Horas mayores a 255", lambda: setattr(c, "horas", (256,0,0,0)))
probar("ID inmutable", lambda: setattr(c, "id", 99))

probar("Vacantes validas", lambda: setattr(s, "vacantes", 2))
probar("Vacantes cero", lambda: setattr(s, "vacantes", 0))
probar("Matricula valida", s.matricular)
probar("Matriculados directos", lambda: setattr(s, "matriculados", 9))
probar("Bajar vacantes", lambda: setattr(s, "vacantes", 0))
probar("Matricula segunda", s.matricular)
probar("Seccion llena", s.matricular)
probar("Retiro valido", s.retirar)
probar("Retiro valido 2", s.retirar)
probar("Retiro sin alumnos", s.retirar)

probar("Plan valido", lambda: p.total_creditos)
probar("Credito negativo", lambda: PlanEstudio("P", 2026,-1,0,0,1,0))
probar("Plan nombre largo", lambda: PlanEstudio("x"*37,2026,1,1,1,1,0))
probar("Bandera invalida", lambda: PlanEstudio("P", 2026,1,1,1,2,0))
probar("Total no editable", lambda: setattr(p, "total_creditos", 500))

probar("Fechas validas", lambda: t.cambiar_fechas(date(2026,8,1), date(2026,12,1)))
probar("Fechas invertidas", lambda: t.cambiar_fechas(date(2026,12,1),date(2026,8,1)))
probar("Matricula invertida", lambda: t.cambiar_fechas_matricula(date(2026,8,1),date(2026,7,1)))
probar("Nota valida", lambda: setattr(t, "nota_minima", 11.5))
probar("Nota mayor a 20", lambda: setattr(t, "nota_minima", 21))
probar("Estado valido", lambda: setattr(t, "estado", 4))
probar("Estado 7", lambda: setattr(t, "estado", 7))

probar("Escuela nombre vacio", lambda: setattr(e, "nombre",""))
probar("Persona abstracta", lambda: Persona("1", "Ana", "Sol"))
a1 = Estudiante("1", "Ana", "Sol", "E1", "27")
d = Docente("2", "Luis", "Rios", "D1")

probar("Nombre completo", lambda: a1.nombre_completo)
probar("Roles", lambda: (a1.rol(), d.rol()))
probar("Lista mixta", lambda: [x.resumen() for x in (c, p, e, t)])

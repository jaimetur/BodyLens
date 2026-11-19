"""Pestañas del libro de datos: las mismas columnas, clave y orden que la hoja de Google del Apps Script
(el Apps Script original, Codigo.gs). La página identifica cada pestaña por su cabecera."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tab:
    name: str
    headers: tuple[str, ...]
    key: int          # columna clave (colClave de guardarFilas_)
    sort: int         # columna por la que se ordena (colOrden)


WITHINGS = Tab("Withings", ("Fecha y hora", "Timestamp", "Peso (kg)", "Grasa (%)", "Masa grasa (kg)", "Músculo (kg)",
                            "Agua (kg)", "Hueso (kg)", "grpid", "attrib"), key=8, sort=1)
ACTIVIDAD = Tab("Actividad", ("Fecha", "Pasos", "Distancia (m)", "Desnivel (m)", "Actividad suave (min)",
                              "Actividad moderada (min)", "Actividad intensa (min)", "Calorías activas",
                              "Calorías totales", "FC media", "FC mínima", "FC máxima", "Origen"), key=0, sort=0)
ENTRENOS = Tab("Entrenamientos", ("ID", "Fecha", "Inicio", "Fin", "Duración (min)", "Tipo", "Calorías", "Pasos",
                                  "Distancia (m)", "FC media", "FC mínima", "FC máxima", "Intensidad"), key=0, sort=2)
SUENO = Tab("Sueño", ("Fecha", "Acostarse", "Levantarse", "En cama (min)", "Dormido (min)", "Ligero (min)",
                      "Profundo (min)", "REM (min)", "Despierto (min)", "Despertares", "Eficiencia (%)", "FC media",
                      "FC mínima", "Origen", "Desvelos"), key=0, sort=0)
SIESTAS = Tab("Siestas", ("ID", "Fecha", "Inicio", "Fin", "Dormido (min)", "Profundo (min)", "REM (min)", "FC media",
                          "Origen"), key=0, sort=2)
SPO2_VO2 = Tab("SpO2 y VO2", ("Fecha y hora", "Timestamp", "SpO2 (%)", "VO2 máx", "Grupo"), key=4, sort=1)
ECG = Tab("ECG", ("Fecha y hora", "Timestamp", "FC (lpm)", "Clasificación", "Señal ID", "Muestreo (Hz)",
                  "Señal (µV)", "Modelo"), key=1, sort=1)
SALUD = Tab("Salud", ("Fecha y hora", "Métrica", "Valor", "Mín", "Máx", "Unidad", "Origen", "Clave"), key=7, sort=0)
AVISOS = Tab("Avisos de salud", ("Inicio", "Fin", "Tipo", "Detalle", "Clave"), key=4, sort=0)
REGISTROS = Tab("Registros de salud", ("Inicio", "Fin", "Registro", "Valor", "Clave"), key=4, sort=0)
FASES = Tab("Sueño Salud (fases)", ("Inicio", "Fin", "Fase", "Origen", "Clave"), key=4, sort=0)

# pestañas que escribe el servidor (las demás de la hoja se conservan tal cual: Control Diario, notas, pesos antiguos…)
DYNAMIC: dict[str, Tab] = {t.name: t for t in (WITHINGS, ACTIVIDAD, ENTRENOS, SUENO, SIESTAS, SPO2_VO2, ECG, SALUD,
                                               AVISOS, REGISTROS, FASES)}

ORIGEN_SALUD = "Apple Salud"

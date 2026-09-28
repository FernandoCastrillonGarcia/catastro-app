"""Registro de municipios: la única lista de ciudades de la app (el orden es el del selector).

Contrato de cada ciudad y receta para agregar una: ARQUITECTURA.md, sección 5.
`sin_dato` explica, por variable, por qué la ciudad no la tiene (FUENTES_VARIABLES.md); lo que
no aparece ahí y falta en un predio se muestra como "sin dato en la fuente".
"""
from . import barranquilla, bogota, bucaramanga, cali, manizales, medellin

SIN_CIIU = ("Ninguna fuente oficial pública liga una dirección con una actividad CIIU (el "
            "catastro clasifica por uso, no por CIIU; revisado 2026-09-27).")
SIN_ESTRUCTURA = "El gestor no publica el material de la estructura (revisado 2026-09-27)."

MUNICIPIOS = {
    "Bogotá": {
        "gestor": "Catastro Bogotá (UAECD)",
        "consultar": bogota.consultar,
        "nombre_codigo": "Lote",
        "sin_dato": {"ciiu": SIN_CIIU},
    },
    "Medellín": {
        "gestor": "Catastro de Medellín (Subsecretaría de Catastro del Distrito)",
        "consultar": medellin.consultar,
        "nombre_codigo": "CBML",
        "sin_dato": {
            "anio": "El campo existe en los servicios del geovisor MapGIS, pero está vacío en más "
                    "del 99,9 % de las construcciones (revisado 2026-09-27). La ficha catastral "
                    "(con usuario) trae la edad: https://www.medellin.gov.co/es/tramites-y-"
                    "servicios/ficha-catastral-predio/",
            "estructura": SIN_ESTRUCTURA,
            "ciiu": SIN_CIIU,
        },
    },
    "Cali": {
        "gestor": "Subdirección de Catastro, Departamento Administrativo de Hacienda de Cali",
        "consultar": cali.consultar,
        "nombre_codigo": "NPN",
        "sin_dato": {
            "anio": "El Geoportal Catastral y la IDESC no publican el año de construcción "
                    "(revisado 2026-09-26). Certificado catastral en el CAM: https://www.cali."
                    "gov.co/hacienda/publicaciones/164112/como-tramitar-facil-y-rapido-su-"
                    "certificado-catastral/",
            "estructura": SIN_ESTRUCTURA,
            "ciiu": SIN_CIIU,
        },
    },
    "Barranquilla": {
        "gestor": "Gerencia de Gestión Catastral de Barranquilla",
        "consultar": barranquilla.consultar,
        "nombre_codigo": "NPN",
        "sin_dato": {
            "anio": "Las capas abiertas de la Alcaldía tienen el campo vacío, y el servicio que sí "
                    "lo trae bloquea las consultas automáticas (Cloudflare, revisado 2026-09-27). "
                    "«Identifica tu predio»: https://catastro.barranquilla.gov.co/identifica-tu-"
                    "predio/",
            "estructura": SIN_ESTRUCTURA,
            "ciiu": SIN_CIIU,
        },
    },
    "Bucaramanga": {
        "gestor": "Área Metropolitana de Bucaramanga (AMB)",
        "consultar": bucaramanga.consultar,
        "nombre_codigo": "Número predial (registro 2021)",
        "sin_dato": {
            "anio": "Los datos catastrales abiertos del AMB tienen el campo de año vacío en todos "
                    "los registros (revisado 2026-09-26). Visor catastral (con sesión): "
                    "https://www.amb.gov.co/consultas-catastro/",
            "estructura": SIN_ESTRUCTURA,
            "ciiu": SIN_CIIU,
        },
    },
    "Manizales": {
        "gestor": "MASORA (por contrato con el municipio); datos del reporte nacional del IGAC",
        "consultar": manizales.consultar,
        "nombre_codigo": "NPN",
        "sin_dato": {
            "anio": "El reporte nacional del IGAC trae el año vacío y la consulta de MASORA exige "
                    "registro, captcha y pago (revisado 2026-09-26): https://masora.gov.co/"
                    "gestion-catastral-manizales/",
            "estructura": SIN_ESTRUCTURA,
            "ciiu": SIN_CIIU,
        },
    },
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
procesador_entrega.py

Entrega: Taller Evaluativo - Informática 2 (Unidad 3)
Referencia de la consigna: Instrucciones del taller.pdf
(En mi entorno: /mnt/data/Instrucciones del taller.pdf)

Resumen:
 - Archivo único ejecutable por doble clic o por terminal.
 - Escanea la carpeta 'dicoms' junto al script (crea la carpeta si no existe).
 - Carga archivos DICOM válidos usando pydicom.
 - Extrae metadatos solicitados por la consigna.
 - Calcula IntensidadPromedio sobre pixel_array si existe.
 - Estructura la información en un pandas.DataFrame.
 - Guarda resultados en CSV y Excel.
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple, Optional, Dict, Any

# Dependencias: pydicom, numpy, pandas, openpyxl (para Excel)
try:
    import pydicom
    from pydicom.errors import InvalidDicomError
except Exception:
    print("ERROR: Falta la librería 'pydicom'. Instala con: pip install pydicom")
    raise SystemExit(1)

try:
    import numpy as np
except Exception:
    print("ERROR: Falta la librería 'numpy'. Instala con: pip install numpy")
    raise SystemExit(1)

try:
    import pandas as pd
except Exception:
    print("ERROR: Falta la librería 'pandas' (y openpyxl para Excel). Instala con: pip install pandas openpyxl")
    raise SystemExit(1)


class ProcesadorDICOM:
    """
    Clase responsable del pipeline completo:
    - Carga de archivos DICOM desde carpeta
    - Extracción de metadatos
    - Cálculo de intensidad promedio
    - Creación y guardado del DataFrame con resultados
    """

    # Mapeo: nombre de atributo DICOM -> nombre de columna en DataFrame
    TAGS: Dict[str, Tuple[str, str]] = {
        "PatientID": ("PatientID", "IdentificadorPaciente"),
        "PatientName": ("PatientName", "NombrePaciente"),
        "StudyInstanceUID": ("StudyInstanceUID", "UIDEstudio"),
        "StudyDescription": ("StudyDescription", "DescripcionEstudio"),
        "StudyDate": ("StudyDate", "FechaEstudio"),
        "Modality": ("Modality", "Modalidad"),
        "Rows": ("Rows", "Filas"),
        "Columns": ("Columns", "Columnas"),
    }

    def __init__(self,
                 dicoms_folder: Optional[str] = None,
                 salida_csv: Optional[str] = None,
                 salida_excel: Optional[str] = None,
                 verbose: bool = True):
        """
        Inicializa rutas y opciones.
        Si no se pasa dicoms_folder, por defecto será ./dicoms al mismo nivel que el script.
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dicoms_folder = dicoms_folder or os.path.join(self.base_dir, "dicoms")
        self.salida_csv = salida_csv or os.path.join(self.base_dir, "resultados_dicom.csv")
        self.salida_excel = salida_excel or os.path.join(self.base_dir, "resultados_dicom.xlsx")
        self.verbose = verbose

    # --------------------------
    # Utilidades internas
    # --------------------------
    def _log(self, *args, **kwargs) -> None:
        """Imprime mensajes solo si verbose=True."""
        if self.verbose:
            print(*args, **kwargs)

    def asegurar_carpeta_dicoms(self) -> bool:
        """
        Crea la carpeta dicoms si no existe. Devuelve True si ya existía o se creó.
        Si no existía, se le indica al usuario que coloque archivos y se devuelve False.
        """
        if not os.path.exists(self.dicoms_folder):
            os.makedirs(self.dicoms_folder, exist_ok=True)
            self._log("Se creó la carpeta de trabajo para DICOMs en:", self.dicoms_folder)
            self._log("Por favor coloca tus archivos DICOM dentro de esa carpeta y vuelve a ejecutar.")
            return False
        return True

    # --------------------------
    # Listado y verificación
    # --------------------------
    def listar_archivos(self) -> List[str]:
        """Lista recursivamente todos los archivos dentro de la carpeta dicoms."""
        rutas: List[str] = []
        for raiz, _, archivos in os.walk(self.dicoms_folder):
            for nombre in archivos:
                rutas.append(os.path.join(raiz, nombre))
        return rutas

    def verificar_es_dicom(self, ruta: str) -> bool:
        """
        Verifica si un archivo es DICOM intentando una lectura ligera del header.
        Retorna True si pydicom lo reconoce.
        """
        try:
            pydicom.dcmread(ruta, stop_before_pixels=True, force=False)
            return True
        except InvalidDicomError:
            return False
        except Exception:
            # otros errores: permisos, archivo corrupto, se consideran no válidos
            return False

    # --------------------------
    # Carga de datasets
    # --------------------------
    def cargar_datasets(self) -> List[Tuple[str, pydicom.dataset.FileDataset]]:
        """
        Devuelve una lista de tuplas (ruta, dataset) solo para DICOMs válidos.
        """
        rutas = self.listar_archivos()
        datasets: List[Tuple[str, pydicom.dataset.FileDataset]] = []

        if not rutas:
            self._log("No se encontraron archivos en la carpeta:", self.dicoms_folder)
            return datasets

        for ruta in rutas:
            if not os.path.isfile(ruta):
                continue
            try:
                if not self.verificar_es_dicom(ruta):
                    self._log(f"  - No DICOM (omitido): {ruta}")
                    continue
                ds = pydicom.dcmread(ruta, force=False)  # lectura completa
                datasets.append((ruta, ds))
                self._log(f"  ✓ DICOM cargado: {ruta}")
            except InvalidDicomError:
                self._log(f"  - InvalidDicomError (omitido): {ruta}")
            except Exception as e:
                self._log(f"  - Error leyendo {ruta}: {e}")

        self._log(f"\nTotal DICOM válidos cargados: {len(datasets)}")
        return datasets

    # --------------------------
    # Extracción de metadatos
    # --------------------------
    def extraer_metadatos(self, ds: pydicom.dataset.FileDataset) -> Dict[str, Optional[str]]:
        """
        Extrae los metadatos requeridos. Si falta alguno, devuelve None para esa columna.
        """
        fila: Dict[str, Optional[str]] = {}
        for _, (attr, col_name) in self.TAGS.items():
            try:
                if hasattr(ds, attr):
                    valor = getattr(ds, attr)
                    fila[col_name] = str(valor)
                else:
                    fila[col_name] = None
            except Exception:
                fila[col_name] = None
        return fila

    # --------------------------
    # Análisis de la imagen
    # --------------------------
    def intensidad_promedio(self, ds: pydicom.dataset.FileDataset) -> Optional[float]:
        """
        Si el dataset contiene pixel_array, calcula la media de sus valores.
        Retorna None en caso de no disponibilidad o error.
        """
        try:
            if hasattr(ds, "pixel_array"):
                arr = np.asarray(ds.pixel_array, dtype=float)
                if arr.size == 0:
                    return None
                return float(np.nanmean(arr))
            return None
        except Exception:
            return None

    # --------------------------
    # Pipeline principal
    # --------------------------
    def procesar(self) -> pd.DataFrame:
        """
        Ejecuta todo el flujo y retorna el DataFrame final. Guarda CSV y Excel.
        """
        # 1) Verificar carpeta dicoms
        if not self.asegurar_carpeta_dicoms():
            # carpeta creada ahora; pedimos al usuario que agregue archivos y terminamos.
            return pd.DataFrame()

        # 2) Cargar DICOMs válidos
        cargas = self.cargar_datasets()
        filas: List[Dict[str, Any]] = []

        # 3) Extraer metadatos y calcular intensidad
        for ruta, ds in cargas:
            metadatos = self.extraer_metadatos(ds)
            intensidad = self.intensidad_promedio(ds)
            fila = {"Archivo": ruta, **metadatos, "IntensidadPromedio": intensidad}
            filas.append(fila)

        df = pd.DataFrame(filas)

        # Garantizar orden y columnas esperadas (incluso si df está vacío)
        columnas_ordenadas = ["Archivo"] + [self.TAGS[k][1] for k in self.TAGS.keys()] + ["IntensidadPromedio"]
        for c in columnas_ordenadas:
            if c not in df.columns:
                df[c] = None
        df = df[columnas_ordenadas]

        # 4) Guardar
        try:
            df.to_csv(self.salida_csv, index=False)
            self._log(f"\nCSV guardado en: {self.salida_csv}")
        except Exception as e:
            self._log("ERROR guardando CSV:", e)

        try:
            df.to_excel(self.salida_excel, index=False)
            self._log(f"Excel guardado en: {self.salida_excel}")
        except Exception as e:
            self._log("ERROR guardando Excel (¿openpyxl instalado?):", e)

        self._log("\nProcesamiento finalizado correctamente.")
        return df


# --------------------------
# Punto de entrada
# --------------------------
def main() -> None:
    """
    Al ejecutarse por doble clic o por línea de comandos, este main inicia el procesador.
    """
    # Si deseas, puedes cambiar verbose a False antes de entregar.
    procesador = ProcesadorDICOM(verbose=True)
    df = procesador.procesar()

    # Informe breve al usuario
    if df.empty:
        print("\nNo se generó DataFrame (posiblemente no había archivos DICOM en 'dicoms').")
    else:
        print("\nResumen del DataFrame generado (primeras 5 filas):")
        with pd.option_context('display.max_columns', None, 'display.width', 200):
            print(df.head(5))

    print("\nProceso finalizado. Los archivos de salida están en la misma carpeta que el script.")

    # En Windows, al ejecutar por doble clic la ventana se cierra rápidamente; mantenerla abierta
    if sys.platform.startswith("win"):
        try:
            input("\nPresiona ENTER para cerrar...")
        except Exception:
            pass


if __name__ == "__main__":
    main()

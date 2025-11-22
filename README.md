# Procesador DICOM - Taller Evaluativo (Informática 2, Unidad 3)

**Integrante(s):** Cristina Isabel Salazar Gómez  
**Monitor:** Juan Esteban Pineda Lopera (jesteban.pineda1@udea.edu.co)  
**Referencia del enunciado:** `Instrucciones del taller.pdf` (archivo adjunto)

---

## Descripción breve

Este proyecto implementa un procesador automático de archivos DICOM en **un único archivo Python** (`procesador_entrega.py`).  
El script:

- Escanea la carpeta `dicoms/` (ubicada junto al script) de forma recursiva.
- Carga archivos DICOM válidos.
- Extrae los metadatos exigidos: `PatientID`, `PatientName`, `StudyInstanceUID`, `StudyDescription`, `StudyDate`, `Modality`, `Rows`, `Columns`.
- Maneja la ausencia de tags (retorna `None` si faltan).
- Calcula `IntensidadPromedio` usando `numpy` sobre `pixel_array` cuando esté disponible.
- Estructura los resultados en un `pandas.DataFrame`.
- Guarda automáticamente `resultados_dicom.csv` y `resultados_dicom.xlsx` en la carpeta del script.

El proyecto fue desarrollado cumpliendo estrictamente los requerimientos del taller (POO, manejo de errores, documentación y salida en CSV/Excel).

---

## Instrucciones de uso

1. Clona o descarga este repositorio en tu equipo.
2. Coloca los archivos DICOM dentro de la carpeta `dicoms/` (si no existe, el script la crea).
3. Instala dependencias (recomendado en un entorno virtual):
   ```bash
   pip install pydicom numpy pandas openpyxl

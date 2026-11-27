# Guía de Contribución — Mi Trámite Justo (Equipo *Los bots*)

¡Gracias por contribuir a democratizar el acceso a trámites públicos!

## Reglas Obligatorias antes de hacer `git push` o abrir un Pull Request

1. **Privacidad por Diseño (PII):** Nunca subas fotografías reales de documentos (INE, CURP, Actas), datos personales ni llaves reales al repositorio.
2. **Accesibilidad WCAG AAA:** Toda mejora de interfaz debe mantener contraste >= 7:1, botones >= 56dp/px, español ciudadano sencillo sin jerga técnica y soporte de voz.
3. **Offline-First:** Ningún módulo puede depender obligatoriamente de conexión a internet para abrir o completar un trámite guardado.
4. **Verificación previa:**
   ```bash
   ruff check src tests scripts main.py
   pytest -v
   ```
5. **Agregar una nueva lengua originaria:** Coloca el nuevo archivo `<idioma>.json` dentro de `assets/languages/` siguiendo el esquema de `nah_puebla.json` y `tot_sierra.json`, sin modificar lógica de código.

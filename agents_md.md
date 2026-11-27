# AGENTS.md — Reglas de Ingeniería para "Mi Trámite Justo" (Web PWA)

Este archivo define el contexto, la arquitectura, las restricciones de despliegue y las reglas obligatorias de programación para cualquier agente de IA que colabore en el desarrollo de **Mi Trámite Justo**.

---

## 1. Contexto y Misión del Proyecto

**Mi Trámite Justo** (Equipo *Los bots*) es una aplicación web progresiva (PWA) con enfoque *mobile-first* diseñada para democratizar el acceso a trámites oficiales, salud, educación y empleo en México (con foco inicial en Puebla).

- **Población objetivo:** Adultos mayores, hablantes de lenguas originarias (náhuatl, totonaco y futuras variantes) con tradición principalmente oral, migrantes, estudiantes de primera generación y comunidades con conectividad nula o intermitente.
- **Propuesta de valor:** Convertir información burocrática confusa en acciones claras y autónomas mediante:
  1. **Puente Lingüístico:** Traducción accesible Español ↔ Náhuatl / Totonaco (texto y audio).
  2. **Intérprete de Documentos:** Escaneo/carga de documentos oficiales para identificar qué son, su propósito en lenguaje sencillo y la acción requerida.
  3. **Modo Sin Conexión (Offline-First):** Descarga y consulta local de guías, requisitos y listas de verificación.
  4. **Guía Interactiva Paso a Paso:** Flujo guiado con máquina de estados, pictogramas, progreso guardado y lectura por voz.

---

## 2. Restricciones Críticas de Despliegue (GitHub Pages EDU - Repo Privado)

La aplicación **DEBE** funcionar como un sitio 100% estático alojado en **GitHub Pages** (repositorio privado habilitado mediante GitHub Education).

- **Cero dependencia de backend propio:** No generar servidores Node.js, Go, Python ni bases de datos remotas obligatorias. Toda la lógica crítica (OCR, clasificación, FSM, traducciones base y almacenamiento) se ejecuta en el navegador (*Edge Client*).
- **Rutas y assets seguros:**
  - Configurar `base` dinámicamente en el bundler (ej. `base: '/<nombre-del-repo>/'` o `./`) para evitar rutas rotas en subdirectorios de GitHub Pages.
  - Utilizar `HashRouter` (o estrategia equivalente compatible con hosting estático) para prevenir errores `404` al recargar rutas internas.
  - Cargar assets estáticos (`svg`, `json`, `opus`/`mp3`) usando rutas relativas a `import.meta.env.BASE_URL`.
- **Seguridad en repositorio y cliente:**
  - Nunca hardcodear claves de API ni credenciales en el código fuente.
  - Cualquier integración opcional en la nube (ej. NMT avanzado online) debe abstraerse detrás de una interfaz desacoplada con *fallback* automático e inmediato al motor local offline.
- **CI/CD:** Mantener un workflow en `.github/workflows/deploy.yml` que ejecute `lint`, `typecheck`, `test` y `build` antes de publicar en GitHub Pages mediante `actions/deploy-pages`.

---

## 3. Stack Tecnológico Obligatorio (Adaptación Web PWA)

Para trasladar los principios de bajo consumo y operación offline al entorno web estático, utilizar:

- **Core:** React 18+ con TypeScript en modo estricto (`"strict": true`) y **Vite** como bundler.
- **Estilos:** Tailwind CSS (mobile-first, utilidades de alto contraste y escalado tipográfico).
- **PWA y Offline:** `vite-plugin-pwa` (Workbox) para precacheo de la app shell, Service Worker y soporte instalable en Android/iOS.
- **Persistencia Local:** `IndexedDB` (mediante `Dexie.js` o `idb`) para guardar progreso de trámites (FSM), preferencias de accesibilidad y paquetes descargados offline. Usar `localStorage` únicamente para banderas ligeras no sensibles.
- **Edge AI / OCR en navegador:**
  - Procesamiento de imagen local mediante HTML5 `<canvas>` (escala de grises, mejora de contraste, recorte).
  - Extracción de texto local con `Tesseract.js` (WebAssembly, cargado de forma diferida/lazy para no penalizar el arranque inicial).
  - Clasificación de documentos y detección de términos burocráticos mediante motor local determinista (Regex + diccionarios semánticos + NER ligero en TypeScript).
- **Audio y Voz:**
  - Web Speech API (`SpeechSynthesis` / `SpeechRecognition`) para español.
  - Reproductor HTML5 Audio ligero con archivos comprimidos (`.opus` / `.webm` / `.mp3` a baja tasa de bits) para narraciones en Náhuatl y Totonaco.
- **Búsqueda Offline:** Búsqueda difusa ligera (ej. `Fuse.js` o algoritmo propio) sobre diccionarios JSON locales.

---

## 4. Arquitectura y Estructura de Directorios

Respetar una arquitectura limpia y desacoplada por responsabilidades. No mezclar lógica de negocio, OCR o acceso a IndexedDB dentro de componentes visuales.

```text
src/
├── app/                  # Configuración de rutas, providers (Audio, Offline, Tema)
├── core/                 # Lógica de dominio pura (sin dependencias de React)
│   ├── fsm/              # Motor de Máquina de Estados Finitos para trámites
│   ├── ocr/              # Pipeline local: preprocesado Canvas + Tesseract WASM
│   ├── nlp/              # Clasificador de documentos, extractor PII seguro y simplificador burocrático
│   └── translation/      # Motor dual (Offline: memorias + fuzzy search | Online: adaptador opcional)
├── data/                 # Almacenamiento local y catálogos estáticos
│   ├── db/               # Esquema IndexedDB (progreso, paquetes offline, preferencias)
│   ├── packs/            # Paquetes modulares de trámites (workflow.json) y glosarios
│   └── languages/        # Language Packs desacoplados (es, nah, tot)
├── features/             # Módulos funcionales de UI
│   ├── home/             # Pantalla principal (4 módulos grandes y claros)
│   ├── translator/       # 1. Puente Lingüístico (Voz/Texto)
│   ├── document-scanner/ # 2. Intérprete de Documentos Oficiales
│   ├── offline-hub/      # 3. Gestor de Descargas y Modo Sin Conexión
│   └── guided-steps/     # 4. Guía Interactiva Paso a Paso (FSM + Audio + SVG)
├── components/ui/        # Sistema de diseño accesible (Botones grandes, AudioPlayer, PictogramCard)
└── styles/               # Tokens de color, tipografía y alto contraste
```

---

## 5. Reglas de los 4 Módulos Principales

### 5.1. Puente Lingüístico (Español ↔ Náhuatl / Totonaco)
- Soportar entrada por texto y voz, y salida en texto y audio.
- Implementar **Arquitectura de Idiomas Desacoplada (*Language Packs*)**: agregar una nueva lengua originaria solo debe requerir añadir un archivo JSON de diccionario/frases y sus clips de audio, sin modificar la lógica del componente.
- En modo offline, conmutar automáticamente a memorias de traducción precalculadas, búsqueda difusa fonética y pistas de audio pregrabadas.

### 5.2. Intérprete de Documentos Oficiales
- Permitir captura desde cámara (`<input type="file" accept="image/*" capture="environment">` o `getUserMedia`) y carga desde galería.
- Flujo obligatorio:
  1. Preprocesamiento local en `<canvas>` (optimización de contraste).
  2. Extracción OCR local (`Tesseract.js` en Web Worker para no congelar la UI).
  3. Identificación del tipo de documento (ej. Acta de Nacimiento, CURP, INE, Comprobante de Domicilio, Citatorio/Carta oficial).
  4. Salida estructurada en **lenguaje ciudadano**:
     - **Qué documento es** (con pictograma).
     - **Para qué sirve** (explicación sencilla).
     - **Acción requerida** (ej. *"Conservar original y entregar copia"*, detección de fechas límite o montos).
     - Botón prominente para **escuchar la explicación en voz alta** y botón para **iniciar guía paso a paso**.

### 5.3. Modo Sin Conexión (Offline-First)
- Mostrar un indicador visual claro del estado de red (En línea / Sin conexión) sin usar alertas intrusivas.
- Permitir descargar y gestionar paquetes de trámites (ej. *Acta de Nacimiento*, *CURP*, *IMSS*, *Pensión Adulto Mayor*) en IndexedDB / Cache API.
- Los trámites descargados deben ser 100% navegables, escuchables y marcables con conexión completamente desactivada (Modo Avión).

### 5.4. Guía Interactiva Paso a Paso (FSM)
- Implementar cada trámite como una **Máquina de Estados Finitos (FSM)** declarativa en JSON (`S01` -> `S02` -> `S03` -> Finalizado).
- Cada paso debe renderizar de forma sincronizada:
  - Barra de progreso visual clara.
  - Ilustración/pictograma vectorial (SVG).
  - Instrucción breve en lenguaje ciudadano (máximo 2-3 líneas por tarjeta).
  - Reproductor de voz automático/manual con resaltado visual del paso actual.
- Persistir el estado actual en IndexedDB en cada transición para retomar el trámite exactamente donde se quedó si el usuario cierra la app.

---

## 6. Reglas de Accesibilidad (Voice-First & Visual-First) y UI/UX

El diseño debe ser utilizable por personas con baja alfabetización, debilidad visual o poca experiencia digital:

- **Identidad visual:**
  - Paleta base inspirada en la marca: verde olivo/bosque (`#4F634B`) y fondo crema cálido (`#FDFBF7`) combinados con acentos institucionales de alto contraste (azul profundo `#1E3A5F` para acciones primarias).
  - Cumplir estrictamente con contraste **WCAG AAA** ($\ge 7:1$ para texto normal, $\ge 4.5:1$ para texto grande).
- **Áreas táctiles:** Todos los botones y controles interactivos deben tener un tamaño mínimo de `56px x 56px` con espaciado generoso (`gap >= 16px`) para evitar toques accidentales.
- **Tipografía y lenguaje:**
  - Tamaño base mínimo de `18px`, escalable con controles de tamaño de letra en la interfaz.
  - Prohibido usar jerga técnica o administrativa en la UI (ej. evitar *"Error 404"*, *"Sincronizar caché"*, *"Acreditar personalidad jurídica"*). Usar siempre español sencillo y directo.
- **Soporte de voz omnipresente:** Toda pantalla y tarjeta informativa debe incluir un botón grande y reconocible de altavoz (`aria-label="Escuchar"`) que lea el contenido en voz alta.
- **Semántica:** Usar HTML semántico (`<main>`, `<nav>`, `<button>`, `<section>`), atributos `aria-live="polite"` para cambios de estado y soporte completo de navegación por teclado.

---

## 7. Privacidad por Diseño (PII) y Rendimiento

- **Cero fuga de datos personales (PII):**
  - Las fotografías de documentos (INE, CURP, Actas) y el texto extraído por OCR **NUNCA** deben enviarse a servidores externos ni imprimirse en `console.log`.
  - Revocar inmediatamente los `ObjectURL` (`URL.revokeObjectURL`) y limpiar el `<canvas>` en cuanto termine el análisis del documento.
  - No almacenar imágenes crudas de documentos del usuario en `localStorage` ni `IndexedDB`.
- **Rendimiento para dispositivos de gama baja:**
  - Implementar *code splitting* (`React.lazy` + `Suspense`) para módulos pesados (especialmente `Tesseract.js` y el escáner).
  - Evitar animaciones costosas; respetar `prefers-reduced-motion`.
  - Mantener el bundle inicial ligero para carga rápida en redes 3G/intermitentes.
  - Ejecutar tareas pesadas (OCR, indexación) en Web Workers para mantener la interfaz fluida a 60 fps.

---

## 8. Convenciones de Código y Flujo de Trabajo del Agente

1. **Idioma:**
   - Código fuente (variables, funciones, tipos, nombres de archivos): **Inglés** (`camelCase` para funciones/variables, `PascalCase` para componentes/tipos, `kebab-case` para carpetas).
   - Textos de interfaz, comentarios de dominio burocrático y documentación de usuario: **Español** (o lenguas originarias en `src/data/languages/`).
2. **Tipado estricto:** Prohibido usar `any`. Definir interfaces explícitas para los esquemas de `WorkflowFSM`, `DocumentAnalysisResult`, `LanguagePack` y `OfflinePackage`.
3. **Datos simulados realistas (Mock Data):** Mientras no exista un corpus comunitario completo, incluir al menos 3 trámites completos en `src/data/packs/` (ej. *Acta de Nacimiento*, *Trámite de CURP*, *Cita/Afiliación IMSS*) y un glosario base Español ↔ Náhuatl/Totonaco claramente marcado como *datos de demostración pendientes de validación comunitaria*.
4. **Verificación obligatoria antes de finalizar cualquier tarea:**
   - Ejecutar `npm run typecheck` (o `tsc --noEmit`) sin errores.
   - Ejecutar `npm run lint` sin advertencias críticas.
   - Ejecutar `npm run test` (pruebas unitarias para el motor FSM, el simplificador burocrático y las utilidades de privacidad/PII).
   - Ejecutar `npm run build` verificando que el resultado en `dist/` funcione bajo una subruta de GitHub Pages.
5. **Prohibiciones para el agente:**
   - No introducir dependencias pesadas innecesarias (ej. librerías gigantes de UI si Tailwind cubre el caso).
   - No romper el funcionamiento offline ni requerir conexión a internet para renderizar la pantalla de inicio o completar un trámite descargado.
   - No omitir el manejo de estados de carga, error amigable y estado vacío (*empty states*).
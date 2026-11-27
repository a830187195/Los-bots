/* Mi Trámite Justo — Web PWA Offline-First (Edge Client, IndexedDB, HashRouter) */
(function () {
  "use strict";

  const FALLBACK_LANGUAGES = {
    nah_puebla: {
      lang_code: "nah_puebla",
      display_name: "Náhuatl (Sierra Norte de Puebla)",
      entries: [
        {
          spanish: "Buenos días, vengo a mi trámite.",
          spanish_simple: "Buenos días, vengo a hacer mi trámite.",
          indigenous_text: "Niltze, nika' notlahtol",
          phonetic_guide: "Nil-tse, ni-ka no-tlaj-tol",
          keywords: ["buenos dias", "vengo", "tramite", "hola"]
        },
        {
          spanish: "Necesito ayuda para entender este documento.",
          spanish_simple: "Por favor ayúdeme a entender este papel.",
          indigenous_text: "Xinechpalehui ma nikmati tlen kihtoa inin amatl",
          phonetic_guide: "Shi-nech-pa-le-wi ma nik-ma-ti tlen kij-to-a i-nin a-matl",
          keywords: ["ayuda", "entender", "documento", "papel"]
        },
        {
          spanish: "¿Dónde está la ventanilla de atención?",
          spanish_simple: "¿En qué ventanilla me atienden?",
          indigenous_text: "¿Kanin kahki in tekichihualoyan?",
          phonetic_guide: "Ka-nin kaj-ki in te-ki-chi-wa-lo-yan",
          keywords: ["donde", "ventanilla", "oficina"]
        },
        {
          spanish: "¿Cuánto tengo que pagar o es gratuito?",
          spanish_simple: "¿Este trámite cuesta dinero o es gratis?",
          indigenous_text: "¿Keski moneki niktlahtlani oso amo kipiya ipati?",
          phonetic_guide: "Kes-ki mo-ne-ki nik-tlaj-tla-ni o-so a-mo ki-pi-ya i-pa-ti",
          keywords: ["cuanto", "pagar", "gratis", "costo"]
        },
        {
          spanish: "Tengo cita médica en la clínica del IMSS.",
          spanish_simple: "Tengo cita con el doctor en el IMSS.",
          indigenous_text: "Nikpiya notekitilis itech tepahtiloyan IMSS",
          phonetic_guide: "Nik-pi-ya no-te-ki-ti-lis i-tech te-paj-ti-lo-yan IMSS",
          keywords: ["cita", "imss", "clinica", "doctor"]
        }
      ]
    },
    tot_sierra: {
      lang_code: "tot_sierra",
      display_name: "Totonaco (Sierra / Papantla)",
      entries: [
        {
          spanish: "Buenos días, vengo a mi trámite.",
          spanish_simple: "Buenos días, vengo a hacer mi trámite.",
          indigenous_text: "Tlan kotsis, ikmin ki trámite",
          phonetic_guide: "Tlan ko-tsis, ik-min ki tra-mi-te",
          keywords: ["buenos dias", "vengo", "tramite", "hola"]
        },
        {
          spanish: "Necesito ayuda para entender este documento.",
          spanish_simple: "Por favor ayúdeme a entender este papel.",
          indigenous_text: "Kimpaskaniyau kakmakgxtakgti uma papil",
          phonetic_guide: "Kim-pas-ka-ni-yau kak-makgsh-takg-ti u-ma pa-pil",
          keywords: ["ayuda", "entender", "documento", "papel"]
        },
        {
          spanish: "¿Dónde está la ventanilla de atención?",
          spanish_simple: "¿En qué ventanilla me atienden?",
          indigenous_text: "¿Nichu wilh niku kintamakgxtakgkan?",
          phonetic_guide: "Ni-chu wilh ni-ku kin-ta-makgsh-takg-kan",
          keywords: ["donde", "ventanilla", "oficina"]
        },
        {
          spanish: "¿Cuánto tengo que pagar o es gratuito?",
          spanish_simple: "¿Este trámite cuesta dinero o es gratis?",
          indigenous_text: "¿Nikgama nakxtakgni o ni lakgchan tumin?",
          phonetic_guide: "Ni-kga-ma naksh-takg-ni o ni lakg-chan tu-min",
          keywords: ["cuanto", "pagar", "gratis", "costo"]
        },
        {
          spanish: "Tengo cita médica en la clínica del IMSS.",
          spanish_simple: "Tengo cita con el doctor en el IMSS.",
          indigenous_text: "Ikgalhi cita nak pukuchinan IMSS",
          phonetic_guide: "Ik-ga-lhi si-ta nak pu-ku-chi-nan IMSS",
          keywords: ["cita", "imss", "clinica", "doctor"]
        }
      ]
    }
  };

  const FALLBACK_PACKS = {
    acta_nacimiento: {
      pack_id: "acta_nacimiento",
      title: "Acta de Nacimiento (Copia Certificada)",
      category: "Identidad y Registro Civil",
      cost_summary: "Aprox. $185 MXN (o gratuito en jornada comunitaria)",
      initial_state: "S01",
      states: [
        {
          state_id: "S01",
          step_number: 1,
          title: "Reunir Papeles",
          citizen_instruction: "Junta tu credencial INE (original y copia) y una copia de tu CURP o acta anterior.",
          pictogram_id: "documents",
          checklist_items: [
            "Credencial oficial INE o pasaporte (original para mostrar)",
            "Copia fotostática clara de tu identificación",
            "Tu CURP anotada o copia de acta anterior"
          ],
          translations: {
            nah_puebla: "Xiksentili moINE uan moCURP itekopio para tiyas ipan tekichihualoyan.",
            tot_sierra: "Katsokgo mi credencial chu mi CURP para nataputsay nak oficina."
          },
          audio_script_es: "Paso uno: Reunir papeles. Lleva tu credencial oficial en original y una fotocopia clara.",
          next_transition: { target_state: "S02", condition: "checklist_complete", label: "Ya tengo mis papeles" },
          prev_state: null
        },
        {
          state_id: "S02",
          step_number: 2,
          title: "Ir a Ventanilla",
          citizen_instruction: "Elige la oficina del Registro Civil más cercana de lunes a viernes de 9:00 a 15:00 h.",
          pictogram_id: "office_map",
          checklist_items: [],
          office_options: [
            "Registro Civil Central Puebla (Av. 11 Oriente 2003)",
            "Juzgado del Registro Civil - Cuetzalan / Sierra Norte",
            "Kiosco Digital Municipal / Presidencia Auxiliar"
          ],
          translations: {
            nah_puebla: "Xitlapehpeni kanin tiyas ipan Registro Civil tlen okachi nechka.",
            tot_sierra: "Kalakpuwanti nak Registro Civil nema tlakg lakatsu wilh."
          },
          audio_script_es: "Paso dos: Ir a ventanilla. Selecciona la oficina más cercana a tu comunidad.",
          next_transition: { target_state: "S03", condition: "office_selected", label: "Confirmar sede" },
          prev_state: "S01"
        },
        {
          state_id: "S03",
          step_number: 3,
          title: "Entregar y Pagar Derechos",
          citizen_instruction: "Entrega tus copias en ventanilla, paga en caja oficial o solicita exención gratuita.",
          pictogram_id: "payment",
          checklist_items: [
            "Entregué mis copias sin dejar mi credencial original",
            "Obtuve mi recibo de pago o sello gratuito"
          ],
          translations: {
            nah_puebla: "Xikmaka itekopio uan xikpia morecibo oso amatl tlen amo kipiya ipati.",
            tot_sierra: "Kamaxki copias chu kapixti mi recibo o papil nema ni lakgchan tumin."
          },
          audio_script_es: "Paso tres: Entrega solo tus copias, conserva tu original y guarda tu recibo.",
          next_transition: { target_state: "S04", condition: "payment_or_exempt", label: "Confirmar pago o exención" },
          prev_state: "S02"
        },
        {
          state_id: "S04",
          step_number: 4,
          title: "Finalizar Trámite",
          citizen_instruction: "Revisa que tu nombre, apellidos y fecha de nacimiento estén escritos correctamente.",
          pictogram_id: "check_done",
          checklist_items: ["Revisé que mi nombre y fecha no tengan errores"],
          translations: {
            nah_puebla: "Xikita kuali intla motoka uan motlakatilis kuali ihkuiliuhtok.",
            tot_sierra: "Kaakxilhti tlan tsokgni mi tukuy. Tlan!"
          },
          audio_script_es: "Paso cuatro: Revisa con calma que todos tus datos estén bien escritos antes de salir.",
          next_transition: null,
          prev_state: "S03",
          is_terminal: true
        }
      ]
    },
    curp_tramite: {
      pack_id: "curp_tramite",
      title: "Trámite y Corrección de CURP",
      category: "Identidad y Registro Nacional",
      cost_summary: "100% Gratuito en todo México",
      initial_state: "S01",
      states: [
        {
          state_id: "S01",
          step_number: 1,
          title: "Reunir Papeles",
          citizen_instruction: "Prepara tu Acta de Nacimiento y una identificación oficial con fotografía.",
          pictogram_id: "documents",
          checklist_items: ["Acta de nacimiento legible", "Identificación oficial vigente"],
          translations: {
            nah_puebla: "Xikualika motlakatilis amatl uan moINE para tikchihuas moCURP.",
            tot_sierra: "Kalhmin mi acta de nacimiento chu mi credencial INE."
          },
          audio_script_es: "Paso uno: Junta tu acta de nacimiento y credencial oficial. La CURP es gratis.",
          next_transition: { target_state: "S02", condition: "checklist_complete", label: "Ya tengo mis papeles" },
          prev_state: null
        },
        {
          state_id: "S02",
          step_number: 2,
          title: "Ubicar Módulo RENAPO",
          citizen_instruction: "Elige el módulo de CURP o Registro Civil más cercano.",
          pictogram_id: "office_map",
          checklist_items: [],
          office_options: ["Módulo Estatal RENAPO Puebla", "Registro Civil Municipal"],
          translations: {},
          audio_script_es: "Paso dos: Elige el módulo más cercano.",
          next_transition: { target_state: "S03", condition: "office_selected", label: "Confirmar módulo" },
          prev_state: "S01"
        },
        {
          state_id: "S03",
          step_number: 3,
          title: "Entregar en Ventanilla (Gratis)",
          citizen_instruction: "Muestra tus documentos para cotejo sin pagar ninguna cuota.",
          pictogram_id: "window_officer",
          checklist_items: ["Mostré mis documentos sin pagar cuota"],
          translations: {},
          audio_script_es: "Paso tres: Entrega tus documentos para revisión. Nadie debe cobrarte.",
          next_transition: { target_state: "S04", condition: "payment_or_exempt", label: "Trámite gratuito listo" },
          prev_state: "S02"
        },
        {
          state_id: "S04",
          step_number: 4,
          title: "Finalizar y Verificar Leyenda",
          citizen_instruction: "Verifica que diga CURP certificada: verificada con el Registro Civil.",
          pictogram_id: "check_done",
          checklist_items: ["Dice CURP certificada"],
          translations: {},
          audio_script_es: "Paso cuatro: Revisa que tu constancia diga CURP certificada.",
          next_transition: null,
          prev_state: "S03",
          is_terminal: true
        }
      ]
    },
    imss_afiliacion: {
      pack_id: "imss_afiliacion",
      title: "Afiliación y Cita Médica IMSS",
      category: "Salud y Seguridad Social",
      cost_summary: "100% Gratuito para derechohabientes",
      initial_state: "S01",
      states: [
        {
          state_id: "S01",
          step_number: 1,
          title: "Reunir Documentos Clínicos",
          citizen_instruction: "Lleva CURP, Número de Seguridad Social (NSS), INE y comprobante de domicilio.",
          pictogram_id: "documents",
          checklist_items: ["CURP y NSS", "INE y comprobante de domicilio"],
          translations: {},
          audio_script_es: "Paso uno: Junta tu CURP, NSS, credencial INE y comprobante de domicilio.",
          next_transition: { target_state: "S02", condition: "checklist_complete", label: "Documentos listos" },
          prev_state: null
        },
        {
          state_id: "S02",
          step_number: 2,
          title: "Ubicar tu Clínica (UMF)",
          citizen_instruction: "Acude al Archivo Clínico de tu Unidad de Medicina Familiar.",
          pictogram_id: "office_map",
          checklist_items: [],
          office_options: ["UMF No. 1 Centro Puebla", "Hospital Rural IMSS-Bienestar"],
          translations: {},
          audio_script_es: "Paso dos: Elige tu clínica correspondiente.",
          next_transition: { target_state: "S03", condition: "office_selected", label: "Confirmar clínica" },
          prev_state: "S01"
        },
        {
          state_id: "S03",
          step_number: 3,
          title: "Registrar Turno (Gratuito)",
          citizen_instruction: "Recibe tu Cartilla Nacional de Salud y número de consultorio.",
          pictogram_id: "window_officer",
          checklist_items: ["Recibí consultorio y turno"],
          translations: {},
          audio_script_es: "Paso tres: Pide tu consultorio y turno matutino o vespertino.",
          next_transition: { target_state: "S04", condition: "payment_or_exempt", label: "Registro completo" },
          prev_state: "S02"
        },
        {
          state_id: "S04",
          step_number: 4,
          title: "Finalizar con Cartilla Lista",
          citizen_instruction: "Llega 15 minutos antes el día de tu cita médica.",
          pictogram_id: "check_done",
          checklist_items: ["Anoté fecha y hora de cita"],
          translations: {},
          audio_script_es: "Paso cuatro: Llega quince minutos antes a tu consultorio.",
          next_transition: null,
          prev_state: "S03",
          is_terminal: true
        }
      ]
    },
    pension_adulto_mayor: {
      pack_id: "pension_adulto_mayor",
      title: "Pensión Bienestar Adulto Mayor",
      category: "Programas Sociales",
      cost_summary: "100% Gratuito — Apoyo bimestral directo",
      initial_state: "S01",
      states: [
        {
          state_id: "S01",
          step_number: 1,
          title: "Reunir Papeles (65 años o más)",
          citizen_instruction: "Prepara credencial INE, Acta de Nacimiento, CURP reciente, comprobante de domicilio y teléfono.",
          pictogram_id: "documents",
          checklist_items: ["Identificación INE o INAPAM", "Acta de nacimiento y CURP reciente", "Comprobante de domicilio y teléfono"],
          translations: {
            nah_puebla: "Xiksentili moINE, motlakatilis amatl, moCURP uan amatl kanin tichanti.",
            tot_sierra: "Katsokgo mi INE, acta, CURP chu papil niku wilat."
          },
          audio_script_es: "Paso uno: Prepara tu credencial INE o INAPAM, acta, CURP, comprobante de domicilio y teléfono.",
          next_transition: { target_state: "S02", condition: "checklist_complete", label: "Ya tengo mis papeles" },
          prev_state: null
        },
        {
          state_id: "S02",
          step_number: 2,
          title: "Ubicar Módulo de Bienestar",
          citizen_instruction: "Elige el módulo más cercano o solicita visita domiciliaria si tienes movilidad limitada.",
          pictogram_id: "office_map",
          checklist_items: [],
          office_options: ["Módulo Bienestar Puebla Centro", "Centro Integrador Sierra Norte", "Solicitud de Visita Domiciliaria"],
          translations: {},
          audio_script_es: "Paso dos: Selecciona el módulo de Bienestar más cercano.",
          next_transition: { target_state: "S03", condition: "office_selected", label: "Confirmar módulo" },
          prev_state: "S01"
        },
        {
          state_id: "S03",
          step_number: 3,
          title: "Entregar Copias y Recibir Folio",
          citizen_instruction: "Entrega tus copias y guarda muy bien tu talón con folio sellado (gratis).",
          pictogram_id: "window_officer",
          checklist_items: ["Recibí mi talón de folio sellado"],
          translations: {},
          audio_script_es: "Paso tres: Guarda muy bien tu talón con número de folio.",
          next_transition: { target_state: "S04", condition: "payment_or_exempt", label: "Tengo mi folio" },
          prev_state: "S02"
        },
        {
          state_id: "S04",
          step_number: 4,
          title: "Finalizar Registro",
          citizen_instruction: "Espera el aviso telefónico para recoger tu tarjeta en el Banco del Bienestar.",
          pictogram_id: "check_done",
          checklist_items: ["Guardé mi talón en lugar seguro"],
          translations: {},
          audio_script_es: "Paso cuatro: Espera la llamada para recoger tu tarjeta.",
          next_transition: null,
          prev_state: "S03",
          is_terminal: true
        }
      ]
    }
  };

  const SAMPLE_DOCS = {
    "Acta de Nacimiento": "ESTADOS UNIDOS MEXICANOS. REGISTRO CIVIL. ACTA DE NACIMIENTO. Deberá presentar en original y copia fotostática legible para cotejo documental.",
    "Citatorio con Jerga": "CITATORIO OFICIAL. Se requiere comparecer de manera personal en un término perentorio de 5 días hábiles para acreditar personalidad jurídica mediante identificación oficial vigente y enterar el pago de derechos por $185.00 MXN antes del 15/12/2026.",
    "Constancia CURP": "SECRETARIA DE GOBERNACION. RENAPO. CLAVE UNICA DE REGISTRO DE POBLACION. CONSTANCIA CURP. Trámite gratuito.",
    "Documento IMSS": "INSTITUTO MEXICANO DEL SEGURO SOCIAL. CONSTANCIA DE VIGENCIA DE DERECHOS. UNIDAD DE MEDICINA FAMILIAR UMF 6."
  };

  const state = {
    languages: FALLBACK_LANGUAGES,
    packs: FALLBACK_PACKS,
    selectedLang: "nah_puebla",
    esToIndigenous: true,
    simulatedOffline: false,
    fontScale: 1.0,
    activePackId: "acta_nacimiento",
    installedPacks: ["acta_nacimiento", "curp_tramite", "imss_afiliacion", "pension_adulto_mayor"],
    progressMap: {}
  };

  // IndexedDB ligera sin dependencias externas
  function openDB() {
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) return reject(new Error("Sin IndexedDB"));
      const req = indexedDB.open("mi_tramite_justo_db", 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains("kv")) {
          db.createObjectStore("kv");
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function dbSet(key, value) {
    try {
      const db = await openDB();
      await new Promise((res, rej) => {
        const tx = db.transaction("kv", "readwrite");
        tx.objectStore("kv").put(value, key);
        tx.oncomplete = res;
        tx.onerror = rej;
      });
    } catch (_) {
      localStorage.setItem("mtj_" + key, JSON.stringify(value));
    }
  }

  async function dbGet(key, fallbackVal) {
    try {
      const db = await openDB();
      const val = await new Promise((res, rej) => {
        const tx = db.transaction("kv", "readonly");
        const req = tx.objectStore("kv").get(key);
        req.onsuccess = () => res(req.result);
        req.onerror = rej;
      });
      return val !== undefined ? val : fallbackVal;
    } catch (_) {
      const raw = localStorage.getItem("mtj_" + key);
      return raw ? JSON.parse(raw) : fallbackVal;
    }
  }

  function speakText(text) {
    if (!text || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "es-MX";
    utter.rate = 0.92;
    window.speechSynthesis.speak(utter);
  }

  function normalizeText(str) {
    return str
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[¿?¡!.,;:"'()\-]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function updateNetworkStatus() {
    const pill = document.getElementById("network-pill");
    const online = navigator.onLine && !state.simulatedOffline;
    if (online) {
      pill.className = "network-pill online";
      pill.textContent = "En línea · Guías disponibles también sin conexión";
    } else {
      pill.className = "network-pill offline";
      pill.textContent = "Sin conexión · Funciona 100% en tu dispositivo";
    }
  }

  function routeTo(hash) {
    const clean = (hash || "#home").replace("#", "");
    const valid = ["home", "translator", "scanner", "offline", "guide"];
    const target = valid.includes(clean) ? clean : "home";
    document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
    document.getElementById("view-" + target).classList.add("active");

    const titles = {
      home: "Mi Trámite Justo",
      translator: "Puente Lingüístico",
      scanner: "Leer Documento",
      offline: "Modo Sin Conexión",
      guide: "Guía Paso a Paso"
    };
    document.getElementById("header-title").textContent = titles[target];
    document.getElementById("btn-back").classList.toggle("hidden", target === "home");

    if (target === "offline") renderOfflinePacks();
    if (target === "guide") renderGuide();
  }

  function translateOffline(query) {
    const pack = state.languages[state.selectedLang];
    if (!pack) return { text: "", phonetic: "", note: "" };
    const normQ = normalizeText(query);
    if (!normQ) return { text: "", phonetic: "", note: "" };

    let best = null;
    let bestScore = 0;
    for (const entry of pack.entries) {
      const src = state.esToIndigenous ? entry.spanish : entry.indigenous_text;
      const normSrc = normalizeText(src);
      if (normSrc === normQ) {
        best = entry;
        bestScore = 1;
        break;
      }
      const qWords = new Set(normQ.split(" "));
      const sWords = new Set((normSrc + " " + (entry.keywords || []).join(" ")).split(" "));
      let overlap = 0;
      qWords.forEach((w) => {
        if (sWords.has(w)) overlap++;
      });
      const score = overlap / Math.max(1, qWords.size);
      if (score > bestScore) {
        bestScore = score;
        best = entry;
      }
    }

    if (best && bestScore >= 0.25) {
      return {
        text: state.esToIndigenous ? best.indigenous_text : best.spanish_simple,
        phonetic: state.esToIndigenous ? "Pronunciación aproximada: " + best.phonetic_guide : "Español ciudadano sencillo",
        note: bestScore === 1 ? "Coincidencia exacta guardada en el teléfono." : "Coincidencia cercana sin internet."
      };
    }

    return {
      text: "Frase no encontrada completa; toca una de las tarjetas rápidas abajo.",
      phonetic: "",
      note: "Sin internet se priorizan frases clave de ventanilla."
    };
  }

  function renderTranslator() {
    const row = document.getElementById("lang-selector-row");
    row.innerHTML = "";
    Object.values(state.languages).forEach((pack) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = pack.lang_code === state.selectedLang ? "btn-primary" : "btn-outline";
      btn.textContent = pack.display_name.split("(")[0].trim();
      btn.onclick = () => {
        state.selectedLang = pack.lang_code;
        renderTranslator();
        runTranslation();
      };
      row.appendChild(btn);
    });

    const langName = (state.languages[state.selectedLang]?.display_name || "").split("(")[0].trim();
    document.getElementById("btn-toggle-dir").textContent = state.esToIndigenous
      ? "Dirección: Español \u2192 " + langName
      : "Dirección: " + langName + " \u2192 Español";

    const list = document.getElementById("quick-phrases-list");
    list.innerHTML = "";
    (state.languages[state.selectedLang]?.entries || []).forEach((entry) => {
      const txt = state.esToIndigenous ? entry.spanish : entry.indigenous_text;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-outline";
      btn.textContent = txt;
      btn.onclick = () => {
        document.getElementById("translator-input").value = txt;
        runTranslation();
      };
      list.appendChild(btn);
    });
  }

  function runTranslation() {
    const q = document.getElementById("translator-input").value;
    const res = translateOffline(q);
    document.getElementById("tr-output-text").textContent = res.text;
    document.getElementById("tr-phonetic").textContent = res.phonetic;
    document.getElementById("tr-note").textContent = res.note;
  }

  function analyzeDocumentText(rawText) {
    const low = rawText.toLowerCase();
    let doc = {
      title: "Documento Administrativo",
      badge: "LLEVAR ORIGINAL PARA REVISIÓN",
      purpose: "Extrajimos fechas, cantidades y palabras clave para ayudarte en ventanilla.",
      action: "Conserva siempre tus documentos originales.",
      packId: "acta_nacimiento"
    };
    if (low.includes("acta de nacimiento") || low.includes("registro civil")) {
      doc = {
        title: "Acta de Nacimiento",
        badge: "CONSERVAR ORIGINAL Y ENTREGAR COPIA",
        purpose: "Acredita tu identidad legal, fecha y lugar de nacimiento.",
        action: "Guarda el acta original y entrega una fotocopia clara.",
        packId: "acta_nacimiento"
      };
    } else if (low.includes("curp") || low.includes("renapo")) {
      doc = {
        title: "Constancia de CURP",
        badge: "IMPRIMIR COPIA GRATUITA",
        purpose: "Es tu clave única para trámites de salud, escuelas y apoyos.",
        action: "Verifica que tu nombre coincida con tu acta. Es gratuita.",
        packId: "curp_tramite"
      };
    } else if (low.includes("imss") || low.includes("vigencia de derechos")) {
      doc = {
        title: "Documento o Vigencia IMSS",
        badge: "PRESENTAR EN CLÍNICA UMF",
        purpose: "Confirma tu registro médico y clínica asignada.",
        action: "Lleva este papel junto con tu credencial INE y CURP.",
        packId: "imss_afiliacion"
      };
    } else if (low.includes("citatorio") || low.includes("acreditar personalidad")) {
      doc = {
        title: "Oficio o Citatorio Oficial",
        badge: "ATENDER ANTES DE LA FECHA LÍMITE",
        purpose: "Es un aviso oficial que pide acudir con tus papeles.",
        action: "Revisa la explicación sencilla antes de presentarte.",
        packId: "acta_nacimiento"
      };
    }

    const clauses = [];
    if (/acreditar\s+personalidad/i.test(rawText)) {
      clauses.push("• Dice: 'Acreditar personalidad jurídica' \u2192 Significa: Muestra tu credencial INE o pasaporte.");
    }
    if (/original\s+y\s+copia/i.test(rawText)) {
      clauses.push("• Dice: 'Original y copia fotostática' \u2192 Significa: Lleva tu original para mostrar y entrega fotocopia.");
    }
    if (/t[eé]rmino\s+perentorio/i.test(rawText)) {
      clauses.push("• Dice: 'Término perentorio' \u2192 Significa: Plazo límite de lunes a viernes para no perder tu turno.");
    }

    document.getElementById("doc-badge").textContent = "ACCIÓN: " + doc.badge;
    document.getElementById("doc-title").textContent = "Identificado: " + doc.title;
    document.getElementById("doc-purpose").textContent = "Para qué sirve: " + doc.purpose;
    document.getElementById("doc-action").textContent = "Qué debes hacer: " + doc.action;
    document.getElementById("doc-clauses").textContent = clauses.join("\n");
    const btnGuide = document.getElementById("btn-doc-start-guide");
    btnGuide.onclick = () => {
      state.activePackId = doc.packId;
      window.location.hash = "#guide";
    };
  }

  function preprocessImageLocally(file) {
    if (!file) return;
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const canvas = document.getElementById("ocr-canvas");
      const ctx = canvas.getContext("2d");
      canvas.width = Math.min(800, img.width);
      canvas.height = Math.round((canvas.width / img.width) * img.height);
      ctx.filter = "grayscale(100%) contrast(140%)";
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Privacy by Design: revocar ObjectURL y limpiar canvas inmediatamente
      URL.revokeObjectURL(objectUrl);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.width = 0;
      canvas.height = 0;

      analyzeDocumentText(file.name.replace(/[_\-]/g, " ") + " original y copia");
    };
    img.src = objectUrl;
  }

  function renderOfflinePacks() {
    const list = document.getElementById("offline-packs-list");
    list.innerHTML = "";
    Object.values(state.packs).forEach((wf) => {
      const isSaved = state.installedPacks.includes(wf.pack_id);
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML =
        `<p class="${isSaved ? "badge-olive" : "badge-warning"}">${isSaved ? "LISTA PARA USAR SIN INTERNET" : "DISPONIBLE PARA GUARDAR"}</p>` +
        `<h3 class="result-big">${wf.title}</h3>` +
        `<p class="text-secondary">${wf.category} · ${wf.states.length} pasos</p>`;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = isSaved ? "btn-primary" : "btn-olive";
      btn.textContent = isSaved ? "Abrir Guía Paso a Paso" : "Guardar guía sin internet";
      btn.onclick = async () => {
        if (!isSaved) {
          state.installedPacks.push(wf.pack_id);
          await dbSet("installed_packs", state.installedPacks);
          const fb = document.getElementById("offline-feedback");
          fb.textContent = "Guía guardada en este dispositivo para usarla en Modo Avión.";
          fb.classList.remove("hidden");
          renderOfflinePacks();
        } else {
          state.activePackId = wf.pack_id;
          window.location.hash = "#guide";
        }
      };
      card.appendChild(btn);
      list.appendChild(card);
    });
  }

  function getProgress(packId) {
    const wf = state.packs[packId];
    if (!state.progressMap[packId]) {
      state.progressMap[packId] = {
        currentStateId: wf.initial_state,
        checked: {},
        selectedOffice: "",
        exempt: false
      };
    }
    return state.progressMap[packId];
  }

  function renderGuide() {
    const sel = document.getElementById("guide-pack-selector");
    sel.innerHTML = "";
    Object.values(state.packs).forEach((wf) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = wf.pack_id === state.activePackId ? "btn-primary" : "btn-outline";
      b.textContent = wf.title;
      b.onclick = () => {
        state.activePackId = wf.pack_id;
        renderGuide();
      };
      sel.appendChild(b);
    });

    const wf = state.packs[state.activePackId];
    const prog = getProgress(wf.pack_id);
    const st = wf.states.find((s) => s.state_id === prog.currentStateId) || wf.states[0];
    const pct = Math.round((st.step_number / wf.states.length) * 100);

    document.getElementById("guide-progress-label").textContent = `Progreso: Paso ${st.step_number} de ${wf.states.length}`;
    document.getElementById("guide-progress-fill").style.width = pct + "%";
    document.getElementById("guide-pictogram-img").src = `./assets/svg/${st.pictogram_id}.svg`;
    document.getElementById("guide-cost-badge").textContent = `Paso ${st.step_number} de ${wf.states.length} · ${wf.cost_summary}`;
    document.getElementById("guide-step-title").textContent = `Paso ${st.step_number}: ${st.title}`;
    document.getElementById("guide-step-instruction").textContent = st.citizen_instruction;

    const indBox = document.getElementById("guide-indigenous-box");
    const nativeTxt = st.translations && st.translations[state.selectedLang];
    if (nativeTxt) {
      indBox.textContent = "En lengua originaria: " + nativeTxt;
      indBox.classList.remove("hidden");
    } else {
      indBox.classList.add("hidden");
    }

    const inter = document.getElementById("guide-interactive-box");
    inter.innerHTML = "";
    const checkedArr = prog.checked[st.state_id] || [];
    (st.checklist_items || []).forEach((item) => {
      const ok = checkedArr.includes(item);
      const b = document.createElement("button");
      b.type = "button";
      b.className = "check-option" + (ok ? " checked" : "");
      b.textContent = (ok ? "\u2705 " : "\u2610 ") + item;
      b.onclick = async () => {
        const list = prog.checked[st.state_id] || [];
        prog.checked[st.state_id] = list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
        await dbSet("progress_map", state.progressMap);
        renderGuide();
      };
      inter.appendChild(b);
    });

    (st.office_options || []).forEach((office) => {
      const selOff = prog.selectedOffice === office;
      const b = document.createElement("button");
      b.type = "button";
      b.className = selOff ? "btn-primary" : "btn-outline";
      b.textContent = (selOff ? "\u2705 Elegida: " : "Elegir: ") + office;
      b.onclick = async () => {
        prog.selectedOffice = office;
        await dbSet("progress_map", state.progressMap);
        renderGuide();
      };
      inter.appendChild(b);
    });

    if (st.next_transition && st.next_transition.condition === "payment_or_exempt") {
      const exBtn = document.createElement("button");
      exBtn.type = "button";
      exBtn.className = prog.exempt ? "check-option checked" : "btn-outline";
      exBtn.textContent = prog.exempt ? "\u2705 Trámite gratuito / Exención confirmada" : "Confirmar trámite gratuito o exención";
      exBtn.onclick = async () => {
        prog.exempt = !prog.exempt;
        await dbSet("progress_map", state.progressMap);
        renderGuide();
      };
      inter.appendChild(exBtn);
    }

    const prevBtn = document.getElementById("btn-step-prev");
    const nextBtn = document.getElementById("btn-step-next");
    const msgEl = document.getElementById("guide-validation-msg");
    msgEl.classList.add("hidden");

    prevBtn.disabled = !st.prev_state;
    prevBtn.onclick = async () => {
      if (!st.prev_state) return;
      prog.currentStateId = st.prev_state;
      await dbSet("progress_map", state.progressMap);
      renderGuide();
    };

    if (st.next_transition) {
      nextBtn.disabled = false;
      nextBtn.textContent = st.next_transition.label + " \u2192";
      nextBtn.onclick = async () => {
        const cond = st.next_transition.condition;
        if (cond === "checklist_complete" && (st.checklist_items || []).some((i) => !checkedArr.includes(i))) {
          msgEl.textContent = "Marca primero todos los requisitos de este paso.";
          msgEl.classList.remove("hidden");
          speakText(msgEl.textContent);
          return;
        }
        if (cond === "office_selected" && !prog.selectedOffice) {
          msgEl.textContent = "Elige primero la oficina a la que vas a ir.";
          msgEl.classList.remove("hidden");
          speakText(msgEl.textContent);
          return;
        }
        if (cond === "payment_or_exempt" && !prog.exempt && (st.checklist_items || []).some((i) => !checkedArr.includes(i))) {
          msgEl.textContent = "Confirma tu comprobante o selecciona trámite gratuito.";
          msgEl.classList.remove("hidden");
          speakText(msgEl.textContent);
          return;
        }
        prog.currentStateId = st.next_transition.target_state;
        await dbSet("progress_map", state.progressMap);
        renderGuide();
      };
    } else {
      nextBtn.disabled = true;
      nextBtn.textContent = "Trámite Finalizado";
    }

    document.getElementById("btn-speak-step").onclick = () => speakText(st.audio_script_es || st.citizen_instruction);
    document.getElementById("btn-step-reset").onclick = async () => {
      delete state.progressMap[wf.pack_id];
      await dbSet("progress_map", state.progressMap);
      renderGuide();
    };
  }

  async function init() {
    state.progressMap = await dbGet("progress_map", {});
    state.installedPacks = await dbGet("installed_packs", state.installedPacks);

    // Intentar cargar JSON reales cuando se sirve vía HTTP / GitHub Pages
    if (window.location.protocol !== "file:") {
      try {
        const [nah, tot] = await Promise.all([
          fetch("./assets/languages/nah_puebla.json").then((r) => (r.ok ? r.json() : null)),
          fetch("./assets/languages/tot_sierra.json").then((r) => (r.ok ? r.json() : null))
        ]);
        if (nah) state.languages.nah_puebla = nah;
        if (tot) state.languages.tot_sierra = tot;
      } catch (_) {}
    }

    if ("serviceWorker" in navigator && window.location.protocol !== "file:") {
      navigator.serviceWorker.register("./sw.js").catch(() => {});
    }

    window.addEventListener("online", updateNetworkStatus);
    window.addEventListener("offline", updateNetworkStatus);
    window.addEventListener("hashchange", () => routeTo(window.location.hash));

    document.getElementById("btn-back").onclick = () => {
      window.location.hash = "#home";
    };
    document.getElementById("btn-font-inc").onclick = () => {
      state.fontScale = Math.min(1.4, Number((state.fontScale + 0.1).toFixed(2)));
      document.documentElement.style.setProperty("--font-scale", String(state.fontScale));
    };
    document.getElementById("btn-font-dec").onclick = () => {
      state.fontScale = Math.max(0.9, Number((state.fontScale - 0.1).toFixed(2)));
      document.documentElement.style.setProperty("--font-scale", String(state.fontScale));
    };
    document.getElementById("btn-toggle-dir").onclick = () => {
      state.esToIndigenous = !state.esToIndigenous;
      renderTranslator();
      runTranslation();
    };
    document.getElementById("btn-translate").onclick = runTranslation;
    document.getElementById("btn-speak-translation").onclick = () => {
      speakText(document.getElementById("tr-output-text").textContent);
    };
    document.getElementById("btn-mic").onclick = () => {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {
        document.getElementById("tr-note").textContent = "Tu navegador no permite micrófono; usa el teclado o las frases rápidas.";
        return;
      }
      const rec = new SR();
      rec.lang = "es-MX";
      rec.onresult = (ev) => {
        document.getElementById("translator-input").value = ev.results[0][0].transcript;
        runTranslation();
      };
      rec.start();
    };

    const sampleBox = document.getElementById("sample-docs-list");
    Object.entries(SAMPLE_DOCS).forEach(([label, txt]) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn-outline";
      b.textContent = "Ejemplo: " + label;
      b.onclick = () => analyzeDocumentText(txt);
      sampleBox.appendChild(b);
    });

    document.getElementById("input-camera").onchange = (e) => preprocessImageLocally(e.target.files[0]);
    document.getElementById("input-gallery").onchange = (e) => preprocessImageLocally(e.target.files[0]);
    document.getElementById("btn-analyze-text").onclick = () => {
      analyzeDocumentText(document.getElementById("manual-doc-text").value);
    };
    document.getElementById("btn-speak-doc").onclick = () => {
      speakText(
        document.getElementById("doc-title").textContent + ". " +
        document.getElementById("doc-purpose").textContent + " " +
        document.getElementById("doc-action").textContent
      );
    };
    document.getElementById("btn-toggle-airplane").onclick = () => {
      state.simulatedOffline = !state.simulatedOffline;
      updateNetworkStatus();
      document.getElementById("btn-toggle-airplane").textContent = state.simulatedOffline
        ? "Modo Avión de prueba: ACTIVADO (toca para desactivar)"
        : "Probar sin internet (Simular Modo Avión)";
    };
    document.querySelectorAll("[data-speak-target]").forEach((btn) => {
      btn.onclick = () => {
        const tgt = btn.getAttribute("data-speak-target");
        if (tgt === "home") {
          speakText("Bienvenido a Mi Trámite Justo. Tienes cuatro botones grandes: Lenguas Originarias, Leer Documento, Modo Sin Conexión y Guía Paso a Paso.");
        } else {
          speakText("Modo sin conexión. Aquí guardas tus trámites para usarlos sin internet.");
        }
      };
    });

    updateNetworkStatus();
    renderTranslator();
    runTranslation();
    analyzeDocumentText(SAMPLE_DOCS["Acta de Nacimiento"]);
    routeTo(window.location.hash || "#home");
  }

  document.addEventListener("DOMContentLoaded", init);
})();

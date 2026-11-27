"""Motor Dual de Traducción Español ↔ Náhuatl / Totonaco (Online NMT + Offline 3 niveles)."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from src.config.settings import APP_PATHS
from src.domain.interfaces import CloudGatewayPort, ConnectivityPort
from src.domain.models import (
    LanguageEntry,
    LanguagePack,
    NetworkStatus,
    TranslationResult,
)


class LanguagePackRegistry:
    """Carga paquetes lingüísticos desacoplados desde JSON sin recompilar la app."""

    def __init__(self, search_dirs: tuple[Path, ...] | None = None) -> None:
        self._search_dirs = search_dirs or (APP_PATHS.languages_dir,)
        self._packs: dict[str, LanguagePack] = {}
        self.reload()

    def reload(self) -> None:
        """Escanea directorios de idiomas y registra cualquier nuevo paquete JSON."""
        loaded: dict[str, LanguagePack] = {}
        for directory in self._search_dirs:
            if not directory.exists():
                continue
            for json_file in sorted(directory.glob("*.json")):
                if json_file.name == "manifest.json":
                    continue
                try:
                    raw = json.loads(json_file.read_text(encoding="utf-8"))
                    if "lang_code" not in raw or "entries" not in raw:
                        continue
                    entries = tuple(
                        LanguageEntry(
                            entry_id=item["entry_id"],
                            spanish=item["spanish"],
                            spanish_simple=item.get("spanish_simple", item["spanish"]),
                            indigenous_text=item["indigenous_text"],
                            phonetic_guide=item.get("phonetic_guide", ""),
                            domain_tag=item.get("domain_tag", "general"),
                            audio_clip=item.get("audio_clip", ""),
                            keywords=tuple(item.get("keywords", [])),
                        )
                        for item in raw["entries"]
                    )
                    pack = LanguagePack(
                        lang_code=raw["lang_code"],
                        display_name=raw["display_name"],
                        variant_region=raw.get("variant_region", "General"),
                        version=raw.get("version", "1.0.0"),
                        validation_status=raw.get(
                            "validation_status",
                            "demo_pendiente_validacion_comunitaria",
                        ),
                        entries=entries,
                    )
                    loaded[pack.lang_code] = pack
                except Exception:
                    continue
        self._packs = loaded

    def list_packs(self) -> list[LanguagePack]:
        """Devuelve todos los idiomas originarios disponibles localmente."""
        return list(self._packs.values())

    def get_pack(self, lang_code: str) -> LanguagePack | None:
        """Obtiene un paquete lingüístico por su código."""
        return self._packs.get(lang_code)


class DualTranslationEngine:
    """Orquesta traducción online NMT (cuando hay red) con conmutación automática a Edge Offline."""

    def __init__(
        self,
        registry: LanguagePackRegistry,
        connectivity: ConnectivityPort | None = None,
        cloud_gateway: CloudGatewayPort | None = None,
        allow_cloud: bool = False,
    ) -> None:
        self._registry = registry
        self._connectivity = connectivity
        self._cloud_gateway = cloud_gateway
        self._allow_cloud = allow_cloud
        self._memory_cache: dict[tuple[str, str, str], TranslationResult] = {}

    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        """Traduce texto bidireccionalmente entre Español y cualquier paquete originario."""
        clean_text = text.strip()
        if not clean_text:
            return TranslationResult(
                source_text="",
                translated_text="",
                phonetic_guide="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine_used="offline_memory",
                confidence=0.0,
            )

        if source_lang == target_lang:
            return TranslationResult(
                source_text=clean_text,
                translated_text=clean_text,
                phonetic_guide="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine_used="offline_memory",
                confidence=1.0,
            )

        cache_key = (_normalize_text(clean_text), source_lang, target_lang)
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Ruta Online: solo si la nube está habilitada y hay enlace activo
        if self._should_try_cloud():
            assert self._cloud_gateway is not None
            cloud_result = self._cloud_gateway.translate_nmt(
                clean_text, source_lang, target_lang
            )
            if cloud_result is not None:
                self._memory_cache[cache_key] = cloud_result
                return cloud_result

        # Ruta Offline de 3 niveles: Memoria de traducción + Búsqueda difusa fonética + Clips
        offline_result = self._translate_offline(clean_text, source_lang, target_lang)
        self._memory_cache[cache_key] = offline_result
        return offline_result

    def search_quick_phrases(
        self, lang_code: str, domain_tag: str | None = None
    ) -> list[LanguageEntry]:
        """Lista frases rápidas listas para tocar y reproducir en ventanilla."""
        pack = self._registry.get_pack(lang_code)
        if pack is None:
            return []
        if domain_tag is None or domain_tag == "todos":
            return list(pack.entries)
        return [e for e in pack.entries if e.domain_tag == domain_tag]

    def _should_try_cloud(self) -> bool:
        if not self._allow_cloud or self._cloud_gateway is None:
            return False
        if self._connectivity is None:
            return False
        return self._connectivity.get_network_status() != NetworkStatus.OFFLINE

    def _translate_offline(
        self, clean_text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        pack_code = target_lang if source_lang == "es" else source_lang
        pack = self._registry.get_pack(pack_code)
        if pack is None or not pack.entries:
            return TranslationResult(
                source_text=clean_text,
                translated_text=f"[Paquete '{pack_code}' no descargado aún]",
                phonetic_guide="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine_used="offline_fuzzy",
                confidence=0.0,
                citizen_note="Descarga el paquete de idioma desde Modo Sin Conexión.",
            )

        norm_query = _normalize_text(clean_text)
        phon_query = _phonetic_normalize(clean_text)
        query_tokens = set(phon_query.split())

        best_entry: LanguageEntry | None = None
        best_score = 0.0
        exact_hit = False

        for entry in pack.entries:
            candidate_raw = entry.spanish if source_lang == "es" else entry.indigenous_text
            cand_norm = _normalize_text(candidate_raw)
            if norm_query == cand_norm:
                best_entry = entry
                best_score = 1.0
                exact_hit = True
                break

            cand_phon = _phonetic_normalize(candidate_raw)
            kw_phon = _phonetic_normalize(" ".join(entry.keywords))
            cand_tokens = set(cand_phon.split()) | set(kw_phon.split())

            token_sim = _jaccard(query_tokens, cand_tokens)
            char_sim = _levenshtein_ratio(phon_query, cand_phon)
            substr_bonus = 0.22 if (norm_query in cand_norm or cand_norm in norm_query) else 0.0
            score = min(0.98, (0.55 * char_sim) + (0.45 * token_sim) + substr_bonus)

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry is not None and best_score >= 0.34:
            translated = (
                best_entry.indigenous_text
                if source_lang == "es"
                else best_entry.spanish_simple
            )
            phonetic = best_entry.phonetic_guide if source_lang == "es" else ""
            note = (
                f"Coincidencia exacta ({pack.display_name})."
                if exact_hit
                else f"Sugerencia cercana en memoria local ({int(best_score * 100)}%)."
            )
            return TranslationResult(
                source_text=clean_text,
                translated_text=translated,
                phonetic_guide=phonetic,
                source_lang=source_lang,
                target_lang=target_lang,
                engine_used="offline_memory" if exact_hit else "offline_fuzzy",
                confidence=round(best_score, 2),
                audio_clip=best_entry.audio_clip,
                citizen_note=note,
            )

        return TranslationResult(
            source_text=clean_text,
            translated_text=self._word_glossary_fallback(clean_text, pack, source_lang),
            phonetic_guide="Pronunciación aproximada por palabras clave",
            source_lang=source_lang,
            target_lang=target_lang,
            engine_used="offline_fuzzy",
            confidence=0.2,
            citizen_note="Frase no encontrada completa; usa las tarjetas rápidas de abajo o conéctate para traducción neuronal.",
        )

    @staticmethod
    def _word_glossary_fallback(
        clean_text: str, pack: LanguagePack, source_lang: str
    ) -> str:
        """Reemplaza tokens burocráticos conocidos cuando no coincide una oración entera."""
        words = _normalize_text(clean_text).split()
        glossary: dict[str, str] = {}
        for entry in pack.entries:
            src_words = _normalize_text(
                entry.spanish if source_lang == "es" else entry.indigenous_text
            ).split()
            tgt_words = (
                entry.indigenous_text if source_lang == "es" else entry.spanish_simple
            ).split()
            if len(src_words) <= 2 and tgt_words:
                glossary[src_words[0]] = " ".join(tgt_words)
            for kw in entry.keywords:
                k_norm = _normalize_text(kw)
                if k_norm and k_norm not in glossary:
                    glossary[k_norm] = (
                        entry.indigenous_text if source_lang == "es" else entry.spanish_simple
                    )

        mapped = [glossary.get(w, w) for w in words]
        return " ".join(mapped)


def _normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    no_accents = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    cleaned = re.sub(r"[¿?¡!.,;:\"'()\-]", " ", no_accents)
    return re.sub(r"\s+", " ", cleaned).strip()


def _phonetic_normalize(text: str) -> str:
    """Normalización fonética tolerante a variantes ortográficas Náhuatl / Totonaco."""
    base = _normalize_text(text)
    replacements = (
        ("qu", "k"),
        ("hu", "w"),
        ("uh", "w"),
        ("cu", "kw"),
        ("tl", "t"),
        ("lh", "l"),
        ("tz", "ts"),
        ("ch", "x"),
        ("c", "k"),
        ("z", "s"),
        ("v", "b"),
        ("'", ""),
    )
    for src, dst in replacements:
        base = base.replace(src, dst)
    return base


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    return len(a & b) / float(len(union))


def _levenshtein_ratio(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    prev = list(range(len2 + 1))
    for i, c1 in enumerate(s1, start=1):
        curr = [i]
        for j, c2 in enumerate(s2, start=1):
            cost = 0 if c1 == c2 else 1
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    dist = prev[-1]
    return max(0.0, 1.0 - (dist / float(max(len1, len2))))

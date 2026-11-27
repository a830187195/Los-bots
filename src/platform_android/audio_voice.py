"""Subsistema unificado de Voz (TTS, STT y reproducción Opus/WAV) para Android y Desktop."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

from src.domain.interfaces import AudioVoicePort


class PlatformAudioVoiceService(AudioVoicePort):
    """Gestiona síntesis de voz (TTS), reconocimiento (STT) y clips Opus offline."""

    def __init__(self) -> None:
        self._android_tts = None
        self._android_player = None
        self._desktop_proc: subprocess.Popen[str] | None = None
        self._kivy_sound = None
        self._is_speaking = False
        self._on_status_change: Callable[[str], None] | None = None

    def bind_status_listener(self, listener: Callable[[str], None]) -> None:
        """Permite a la UI mostrar feedback visual sincronizado cuando hay narración activa."""
        self._on_status_change = listener

    def speak(self, text: str, lang_code: str = "es-MX") -> bool:
        """Narra texto en voz alta sin bloquear la interfaz gráfica."""
        clean = text.strip()
        if not clean:
            return False
        self.stop_audio()
        self._notify(f"Narrando: {clean[:48]}...")

        if _is_android_env():
            if self._speak_android(clean, lang_code):
                return True

        return self._speak_desktop(clean)

    def play_audio_file(self, file_path: str) -> bool:
        """Reproduce archivos .opus/.ogg/.wav nativos de forma asíncrona."""
        if not file_path or not Path(file_path).exists():
            return False
        self.stop_audio()

        if _is_android_env():
            try:
                from jnius import autoclass  # type: ignore import-not-found

                MediaPlayer = autoclass("android.media.MediaPlayer")
                player = MediaPlayer()
                player.setDataSource(str(file_path))
                player.prepare()
                player.start()
                self._android_player = player
                self._notify("Reproduciendo audio nativo...")
                return True
            except Exception:
                pass

        try:
            from kivy.core.audio import SoundLoader  # type: ignore import-not-found

            sound = SoundLoader.load(str(file_path))
            if sound is not None:
                sound.play()
                self._kivy_sound = sound
                self._notify("Reproduciendo audio local...")
                return True
        except Exception:
            pass
        return False

    def stop_audio(self) -> None:
        """Detiene cualquier TTS o reproductor en curso."""
        if self._android_tts is not None:
            try:
                self._android_tts.stop()
            except Exception:
                pass
        if self._android_player is not None:
            try:
                self._android_player.stop()
                self._android_player.release()
            except Exception:
                pass
            self._android_player = None
        if self._kivy_sound is not None:
            try:
                self._kivy_sound.stop()
            except Exception:
                pass
            self._kivy_sound = None
        if self._desktop_proc is not None and self._desktop_proc.poll() is None:
            try:
                self._desktop_proc.terminate()
            except Exception:
                pass
            self._desktop_proc = None
        self._is_speaking = False

    def listen_once(
        self,
        lang_code: str,
        on_result: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Captura voz del ciudadano mediante RecognizerIntent en Android o fallback."""
        if _is_android_env() and self._listen_android(lang_code, on_result, on_error):
            return

        # Intento opcional con SpeechRecognition si existe en escritorio
        def _desktop_listen() -> None:
            try:
                import speech_recognition as sr  # type: ignore import-not-found

                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                text = recognizer.recognize_google(audio, language=lang_code)
                on_result(text)
            except Exception:
                on_error(
                    "Usa el teclado o toca una frase rápida abajo (micrófono nativo disponible al compilar APK Android)."
                )

        threading.Thread(target=_desktop_listen, daemon=True).start()

    def _speak_android(self, text: str, lang_code: str) -> bool:
        try:
            from jnius import autoclass  # type: ignore import-not-found

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            Locale = autoclass("java.util.Locale")

            if self._android_tts is None:
                self._android_tts = TextToSpeech(PythonActivity.mActivity, None)

            locale = Locale("es", "MX") if lang_code.startswith("es") else Locale("es", "MX")
            self._android_tts.setLanguage(locale)
            self._android_tts.setSpeechRate(0.92)  # Ligeramente pausado para claridad
            self._android_tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "mtj_utterance")
            self._is_speaking = True
            return True
        except Exception:
            return False

    def _listen_android(
        self,
        lang_code: str,
        on_result: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> bool:
        try:
            from android import activity  # type: ignore import-not-found
            from jnius import autoclass  # type: ignore import-not-found

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")

            REQ_CODE = 8421

            def _on_activity_result(request_code: int, result_code: int, data: object) -> None:
                if request_code != REQ_CODE:
                    return
                activity.unbind(on_activity_result=_on_activity_result)
                Activity = autoclass("android.app.Activity")
                if result_code != Activity.RESULT_OK or data is None:
                    on_error("No se detectó voz; intenta hablar más cerca del micrófono.")
                    return
                matches = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if matches and matches.size() > 0:
                    on_result(str(matches.get(0)))
                else:
                    on_error("No se entendió el audio.")

            activity.bind(on_activity_result=_on_activity_result)
            intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, lang_code)
            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT, "Habla claro para traducir tu consulta..."
            )
            PythonActivity.mActivity.startActivityForResult(intent, REQ_CODE)
            return True
        except Exception:
            return False

    def _speak_desktop(self, text: str) -> bool:
        if sys.platform.startswith("win"):
            safe_text = text.replace("'", "''")
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Rate = -1; "
                f"$s.Speak('{safe_text}')"
            )
            try:
                self._desktop_proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                self._is_speaking = True
                return True
            except Exception:
                return False

        try:
            import pyttsx3  # type: ignore import-not-found

            def _run() -> None:
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.say(text)
                engine.runAndWait()

            threading.Thread(target=_run, daemon=True).start()
            self._is_speaking = True
            return True
        except Exception:
            return False

    def _notify(self, message: str) -> None:
        if self._on_status_change is not None:
            self._on_status_change(message)


def _is_android_env() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ

"""Puente opcional hacia Google ML Kit Text Recognition en Android mediante pyjnius."""

from __future__ import annotations

import os

from src.domain.models import OCRBoundingBox


def try_android_mlkit_ocr(image_bytes: bytes) -> list[OCRBoundingBox]:
    """Ejecuta ML Kit On-Device si el APK incluye la dependencia Gradle de text-recognition."""
    if not image_bytes or not _is_android_env():
        return []
    try:
        import threading

        from jnius import autoclass  # type: ignore import-not-found

        BitmapFactory = autoclass("android.graphics.BitmapFactory")
        InputImage = autoclass("com.google.mlkit.vision.common.InputImage")
        TextRecognition = autoclass("com.google.mlkit.vision.text.TextRecognition")
        TextRecognizerOptions = autoclass(
            "com.google.mlkit.vision.text.latin.TextRecognizerOptions"
        )
        Tasks = autoclass("com.google.android.gms.tasks.Tasks")

        bitmap = BitmapFactory.decodeByteArray(image_bytes, 0, len(image_bytes))
        if bitmap is None:
            return []
        try:
            input_image = InputImage.fromBitmap(bitmap, 0)
            recognizer = TextRecognition.getClient(
                TextRecognizerOptions.DEFAULT_OPTIONS
            )
            result_boxes: list[OCRBoundingBox] = []

            # Await síncrono seguro fuera del hilo principal si es necesario
            def _await_task() -> None:
                vision_text = Tasks.await(recognizer.process(input_image))
                blocks = vision_text.getTextBlocks()
                for i in range(blocks.size()):
                    block = blocks.get(i)
                    rect = block.getBoundingBox()
                    result_boxes.append(
                        OCRBoundingBox(
                            text=str(block.getText()),
                            x=int(rect.left) if rect else 0,
                            y=int(rect.top) if rect else 0,
                            width=int(rect.width()) if rect else 100,
                            height=int(rect.height()) if rect else 24,
                            confidence=0.92,
                        )
                    )

            worker = threading.Thread(target=_await_task)
            worker.start()
            worker.join(timeout=4.0)
            return result_boxes
        finally:
            bitmap.recycle()
    except Exception:
        return []


def _is_android_env() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ

"""
Détection de contenu NSFW sur les images uploadées.

Utilise le modèle Marqo/nsfw-image-detection-384 (Hugging Face),
basé sur timm/vit_tiny_patch16_384, entraîné pour une classification binaire SFW/NSFW.
Voir: https://huggingface.co/Marqo/nsfw-image-detection-384
"""
import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Constantes configurables par variables d'environnement
NSFW_DETECTION_ENABLED = os.getenv("NSFW_DETECTION_ENABLED", "1").strip().lower() in ("1", "true", "yes")
NSFW_THRESHOLD = float(os.getenv("NSFW_THRESHOLD", "0.5"))

# État global pour chargement paresseux du modèle (évite de recharger à chaque requête)
_model: Optional[object] = None
_transforms: Optional[object] = None
_nsfw_class_index: Optional[int] = None


def _get_model_and_transforms():
    """Charge le modèle et les transforms timm (lazy, une seule fois)."""
    global _model, _transforms, _nsfw_class_index
    if _model is not None:
        return _model, _transforms, _nsfw_class_index

    import torch
    import timm
    from PIL import Image

    model = timm.create_model("hf_hub:Marqo/nsfw-image-detection-384", pretrained=True)
    model = model.eval()
    data_config = timm.data.resolve_model_data_config(model)
    transforms = timm.data.create_transform(**data_config, is_training=False)

    class_names = model.pretrained_cfg.get("label_names", ["NSFW", "SFW"])
    class_names_lower = [n.lower() for n in class_names]
    try:
        nsfw_class_index = class_names_lower.index("nsfw")
    except ValueError:
        nsfw_class_index = 0

    logger.info("NSFW class index: %d (label_names=%s)", nsfw_class_index, class_names)

    _model = model
    _transforms = transforms
    _nsfw_class_index = nsfw_class_index
    logger.info("NSFW detector model loaded (Marqo/nsfw-image-detection-384).")
    return _model, _transforms, _nsfw_class_index


def get_nsfw_probability(image_bytes: bytes) -> float:
    """
    Retourne la probabilité que l'image soit NSFW (entre 0 et 1).

    - Entrée: bytes bruts d'une image (JPEG, PNG, etc.).
    - Sortie: float dans [0, 1], où 1 = très probablement NSFW.

    Cette fonction est synchrone et peut être appelée depuis run_in_threadpool.
    """
    import torch
    from PIL import Image

    model, transforms, nsfw_idx = _get_model_and_transforms()
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    tensor = transforms(img).unsqueeze(0)
    with torch.no_grad():
        output = model(tensor).softmax(dim=-1).cpu()
    proba = output[0][nsfw_idx].item()
    return float(proba)


def is_nsfw(image_bytes: bytes, threshold: Optional[float] = None) -> bool:
    """
    Indique si l'image est considérée comme NSFW selon le seuil configuré.

    :param image_bytes: contenu binaire de l'image
    :param threshold: seuil de probabilité NSFW (défaut: NSFW_THRESHOLD)
    :return: True si P(NSFW) >= threshold
    """
    if threshold is None:
        threshold = NSFW_THRESHOLD
    prob = get_nsfw_probability(image_bytes)
    return prob >= threshold

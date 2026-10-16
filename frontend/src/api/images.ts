import { POST_API_BASE_URL } from "./client";

export interface UploadPostImageResponse {
  success: boolean;
  nsfwDetectionEnabled?: boolean;
  nsfwThreshold?: number;
  nsfwProbability?: number;
}

/**
 * Construit l'URL publique de téléchargement/visualisation d'une image liée à une publication.
 */
export function getImageUrl(imageId: string): string {
  if (!imageId) return "";
  if (imageId.startsWith("http://") || imageId.startsWith("https://")) {
    return imageId;
  }
  return `${POST_API_BASE_URL}/images/${encodeURIComponent(imageId)}`;
}

/**
 * Récupère le contenu binaire (Blob) d'une image par son identifiant.
 */
export async function fetchImageBlob(
  imageId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const url = getImageUrl(imageId);
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(
      `Impossible de charger l'image ${imageId} (HTTP ${response.status}).`,
    );
  }
  return response.blob();
}

/**
 * Téléverse une image pour une publication (PUT /api/v1/images/{image_id}).
 *
 * @param imageId Identifiant UUID de l'entité image
 * @param imageFile Fichier image (File ou Blob)
 * @param token Jeton Firebase d'authentification Bearer
 * @param signal Signal d'annulation
 * @returns Résultat de l'opération avec les en-têtes de modération NSFW le cas échéant
 */
export async function uploadPostImage(
  imageId: string,
  imageFile: File | Blob,
  token?: string,
  signal?: AbortSignal,
): Promise<UploadPostImageResponse> {
  const url = getImageUrl(imageId);
  const formData = new FormData();
  formData.append("image", imageFile);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: "PUT",
    headers,
    body: formData,
    signal,
  });

  if (!response.ok) {
    let detail = `Échec de l'envoi de l'image (HTTP ${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson && typeof errorJson.detail === "string") {
        detail = errorJson.detail;
      }
    } catch {
      // pas de corps json
    }
    throw new Error(detail);
  }

  const detectionEnabledHeader = response.headers.get(
    "X-NSFW-Detection-Enabled",
  );
  const thresholdHeader = response.headers.get("X-NSFW-Threshold");
  const probHeader = response.headers.get("X-NSFW-Probability");

  return {
    success: true,
    nsfwDetectionEnabled: detectionEnabledHeader
      ? detectionEnabledHeader === "1"
      : undefined,
    nsfwThreshold: thresholdHeader ? parseFloat(thresholdHeader) : undefined,
    nsfwProbability: probHeader ? parseFloat(probHeader) : undefined,
  };
}

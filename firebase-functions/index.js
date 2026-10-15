/**
 * Cloud Functions 10books :
 * - beforeCreate : custom claims à la création d'un utilisateur.
 * - onCreate : création du document Firestore users/{uid} (réputation, préférences).
 * - onVendorReviewWrite : mise à jour de vendor_reputation quand une review est créée/modifiée/supprimée.
 */
const functions = require("firebase-functions");
const admin = require("firebase-admin");
const jwt = require('jsonwebtoken');

if (!admin.apps.length) {
  admin.initializeApp();
}
const db = admin.firestore();

// ─── Custom claims (beforeCreate) ───────────────────────────────────────────

/**
 * Liste de permissions par défaut pour un utilisateur basic_user.
 * Même logique que la fonction Python get_basic_user_permissions().
 */
function getBasicUserPermissions() {
  const resources = {
    listing: ["create", "update", "delete", "read"],
    transaction: ["create", "read", "update", "cancel"],
    book: ["create", "read", "update", "delete"],
    messaging: ["create", "read", "send", "archive"],
  };
  const permissions = [];
  for (const [resource, actions] of Object.entries(resources)) {
    for (const action of actions) {
      permissions.push(`${resource}:${action}:self`);
    }
  }
  return permissions;
}

/**
 * Blocking Function : s'exécute AVANT la création d'un utilisateur Firebase Auth.
 * Les claims définis ici seront présents dans le tout premier token de l'utilisateur.
 */
exports.beforecreated = functions.auth.user().beforeCreate((user, context) => {
  const permissions = getBasicUserPermissions();
  return {
    customClaims: {
      permissions,
      role: "basic_user",
    },
  };
});

// ─── Firestore : document utilisateur à la création (onCreate) ───────────────

/**
 * Crée le document Firestore users/{uid} à la première création du compte Auth.
 * Champs : vendor_reputation (moyenne + nombre de reviews), preferences (à étendre plus tard).
 */
exports.onUserCreated = functions.auth.user().onCreate(async (user) => {
  await db.collection("users").doc(user.uid).set({
    vendor_reputation: {
      averageRating: 0,
      reviewCount: 0,
    },
    preferences: {},
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
    updatedAt: admin.firestore.FieldValue.serverTimestamp(),
  });
});

// ─── Firestore : mise à jour de la réputation vendeur (vendor_reviews) ───────

/**
 * Convertit une note review (stockée en 0–5 par l'app) vers l'échelle 0–10 (listing-api).
 * Ex: 4.5 étoiles → 9/10.
 */
function normalizeRatingToScale10(rating) {
  if (typeof rating !== "number" || Number.isNaN(rating)) return 0;
  return Math.min(10, Math.max(0, rating * 2));
}

/**
 * Structure : vendor_reviews/{vendorId}/reviews/{reviewId}
 * Chaque review : buyer_id, rating (0–5 étoiles), comment (optionnel), createdAt.
 * Recalcule averageRating (0–10) et reviewCount puis met à jour users/{vendorId}.vendor_reputation.
 * Aligné sur le listing-api qui utilise seller_rep sur 0–10.
 */
async function recalculateVendorReputation(vendorId) {
  const reviewsRef = db.collection("vendor_reviews").doc(vendorId).collection("reviews");
  const snapshot = await reviewsRef.get();
  const reviewCount = snapshot.size;
  const payload = {
    vendor_reputation: {
      averageRating: 0,
      reviewCount,
    },
    updatedAt: admin.firestore.FieldValue.serverTimestamp(),
  };
  if (reviewCount > 0) {
    let sum = 0;
    snapshot.docs.forEach((doc) => {
      const data = doc.data();
      const raw = typeof data.rating === "number" ? data.rating : 0;
      sum += normalizeRatingToScale10(raw);
    });
    payload.vendor_reputation.averageRating = Math.round((sum / reviewCount) * 10) / 10;
  }
  await db.collection("users").doc(vendorId).set(payload, { merge: true });
}

/**
 * Déclenchée à chaque création / mise à jour / suppression d'une review.
 * Recalcule la réputation du vendeur et met à jour users/{vendorId}.
 */
exports.onVendorReviewWrite = functions.firestore
  .document("vendor_reviews/{vendorId}/reviews/{reviewId}")
  .onWrite(async (change, context) => {
    const { vendorId } = context.params;
    try {
      await recalculateVendorReputation(vendorId);
      functions.logger.info("onVendorReviewWrite: updated users/" + vendorId);
    } catch (err) {
      functions.logger.error("onVendorReviewWrite failed for vendorId=" + vendorId, err);
      throw err;
    }
  });

// ─── Firestore : réputation acheteur (buyer_reviews) ──────────────────────────

/**
 * Structure : buyer_reviews/{buyerId}/reviews/{reviewId}
 * Chaque review : vendor_id, rating (0–5 étoiles), comment (optionnel), createdAt.
 * Recalcule buyer_reputation (averageRating 0–10) et met à jour users/{buyerId}.
 */
async function recalculateBuyerReputation(buyerId) {
  const reviewsRef = db.collection("buyer_reviews").doc(buyerId).collection("reviews");
  const snapshot = await reviewsRef.get();
  const reviewCount = snapshot.size;
  const payload = {
    buyer_reputation: {
      averageRating: 0,
      reviewCount,
    },
    updatedAt: admin.firestore.FieldValue.serverTimestamp(),
  };
  if (reviewCount > 0) {
    let sum = 0;
    snapshot.docs.forEach((doc) => {
      const data = doc.data();
      const raw = typeof data.rating === "number" ? data.rating : 0;
      sum += normalizeRatingToScale10(raw);
    });
    payload.buyer_reputation.averageRating = Math.round((sum / reviewCount) * 10) / 10;
  }
  await db.collection("users").doc(buyerId).set(payload, { merge: true });
}

exports.onBuyerReviewWrite = functions.firestore
  .document("buyer_reviews/{buyerId}/reviews/{reviewId}")
  .onWrite(async (change, context) => {
    const { buyerId } = context.params;
    await recalculateBuyerReputation(buyerId);
  });

// ─── Sync réputation Firestore → listing-api (listings) ─────────────────────

/**
 * Quand users/{uid}.vendor_reputation change, met à jour seller_rep
 * pour tous les listings de ce vendeur dans le listing-api (PostgreSQL).
 * LISTING_API_URL doit être configuré (ex. https://listing-api.example.com ou http://listing-api:8000).
 */
function getListingApiUrl() {
  const url = process.env.LISTING_API_URL;
  if (!url) {
    throw new Error("LISTING_API_URL must be set");
  }
  return url.replace(/\/$/, "");
}

/**
 * Retourne seller_rep 0–10 pour le listing-api (averageRating déjà stocké en 0–10).
 */
function averageRatingToSellerRep(averageRating) {
  if (typeof averageRating !== "number" || Number.isNaN(averageRating)) return 0;
  return Math.min(10, Math.max(0, Math.round(averageRating)));
}

/**
 * Déclenchée à chaque mise à jour du document users/{uid}.
 * Si vendor_reputation a changé, appelle le listing-api pour mettre à jour tous les listings du vendeur.
 */


exports.onUserProfileUpdate = functions.runWith({
  secrets: ["INTERNAL_API_SECRET", "LISTING_API_URL"],
}).firestore
  .document("users/{userId}")
  .onUpdate(async (change, context) => {
    const { userId } = context.params;
    const projectId = process.env.GCP_PROJECT || process.env.GCLOUD_PROJECT;
    const secretKey = process.env.INTERNAL_API_SECRET;
    if (!secretKey) {
      throw new Error("INTERNAL_API_SECRET must be set");
    }
    
    const before = change.before.data();
    const after = change.after.data();
    const afterRep = after?.vendor_reputation;
    
    if (!afterRep) return;

    const beforeAvg = before?.vendor_reputation?.averageRating ?? null;
    const afterAvg = afterRep?.averageRating ?? 0;
    const beforeCount = before?.vendor_reputation?.reviewCount ?? null;
    const afterCount = afterRep?.reviewCount ?? 0;

    if (beforeAvg === afterAvg && beforeCount === afterCount) return;

    const payload = {
      uid: "cloud-function-admin",
      sub: "cloud-function-admin",
      iss: `https://securetoken.google.com/${projectId}`,
      aud: projectId,
      iat: Math.floor(Date.now() / 1000),
      permissions: ["admin:update:all"],
      role: "internal_service"
    };

    const token = jwt.sign(payload, secretKey, { 
      expiresIn: '1m',
      algorithm: 'HS256' 
    });

    const sellerRep = averageRatingToSellerRep(afterAvg);
    const baseUrl = getListingApiUrl();
    const url = `${baseUrl}/api/v1/listings/vendor/${userId}/reputation`;

    const res = await fetch(url, {
      method: "PATCH",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ seller_rep: sellerRep }),
    });

    if (!res.ok) {
      throw new Error(`listing-api PATCH ${url} failed: ${res.status} ${await res.text()}`);
    }
  });

// ───────────────────────────────────────────────────────────────────────────────
// Address validation via Cloud Function
// ───────────────────────────────────────────────────────────────────────────────

const GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json";
const USER_PRIVATE_LOCATIONS_COLLECTION = "user_private_locations";

function getGoogleMapsApiKey() {
  return process.env.GOOGLE_MAPS_API_KEY;
}

exports.validateAddress = functions.runWith({
  secrets: ["GOOGLE_MAPS_API_KEY"],
}).https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "Vous devez être connecté pour valider une adresse."
    );
  }

  const rawAddress = typeof data?.address === "string" ? data.address.trim() : "";
  if (rawAddress.length < 3) {
    throw new functions.https.HttpsError(
      "invalid-argument",
      "L'adresse doit contenir au moins 3 caractères."
    );
  }

  const apiKey = getGoogleMapsApiKey();
  if (!apiKey) {
    throw new functions.https.HttpsError(
      "failed-precondition",
      "La clé GOOGLE_MAPS_API_KEY n'est pas configurée."
    );
  }

  const url = new URL(GEOCODE_URL);
  url.searchParams.set("address", rawAddress);
  url.searchParams.set("key", apiKey);

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new functions.https.HttpsError(
      "unavailable",
      "Le service Google Maps est indisponible."
    );
  }

  const payload = await response.json();
  if (payload.status !== "OK" || !Array.isArray(payload.results) || payload.results.length === 0) {
    throw new functions.https.HttpsError(
      "not-found",
      "Adresse introuvable."
    );
  }

  const topResult = payload.results[0];
  const location = topResult.geometry?.location ?? {};
  if (typeof location.lat !== "number" || typeof location.lng !== "number") {
    throw new functions.https.HttpsError(
      "internal",
      "Réponse invalide de Google Maps."
    );
  }

  return {
    verified: true,
    formattedAddress: topResult.formatted_address ?? rawAddress,
    placeId: topResult.place_id ?? "",
    latitude: location.lat,
    longitude: location.lng,
  };
});

function haversineKm(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => deg * (Math.PI / 180);
  const earthRadiusKm = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return earthRadiusKm * c;
}

async function getUserPrivateLocation(uid) {
  const snap = await db.collection(USER_PRIVATE_LOCATIONS_COLLECTION).doc(uid).get();
  if (!snap.exists) return null;
  const data = snap.data() ?? {};
  const latitude = typeof data.latitude === "number" ? data.latitude : null;
  const longitude = typeof data.longitude === "number" ? data.longitude : null;
  if (latitude === null || longitude === null) return null;
  return { latitude, longitude };
}

/**
 * Retourne uniquement la distance (km) entre l'utilisateur courant et un autre user.
 * N'expose jamais les coordonnees brutes.
 */
exports.getDistanceToUser = functions.https.onCall(async (data, context) => {
  if (!context.auth?.uid) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "Vous devez etre connecte pour calculer une distance."
    );
  }

  const otherUserId = typeof data?.userId === "string" ? data.userId.trim() : "";
  if (!otherUserId) {
    throw new functions.https.HttpsError(
      "invalid-argument",
      "Le userId cible est requis."
    );
  }

  if (otherUserId === context.auth.uid) {
    return { distanceKm: 0 };
  }

  const [fromLocation, toLocation] = await Promise.all([
    getUserPrivateLocation(context.auth.uid),
    getUserPrivateLocation(otherUserId),
  ]);

  if (!fromLocation || !toLocation) {
    return { distanceKm: null };
  }

  const distanceKm = haversineKm(
    fromLocation.latitude,
    fromLocation.longitude,
    toLocation.latitude,
    toLocation.longitude
  );

  return { distanceKm: Math.round(distanceKm * 10) / 10 };
});

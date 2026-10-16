export const BASE_IP = "localhost:8080";
export const POST_API_BASE_URL = `http://post.${BASE_IP}/api/v1`;
export const MESSAGING_API_BASE_URL = `http://messaging.${BASE_IP}/api/v1`;

export function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  return fetch(`${POST_API_BASE_URL}/${path.replace(/^\/+/, "")}`, options);
}

export function messagingApiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  return fetch(
    `${MESSAGING_API_BASE_URL}/${path.replace(/^\/+/, "")}`,
    options,
  );
}

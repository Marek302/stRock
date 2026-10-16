-- À appliquer sur une base existante avant de démarrer l'API mise à jour.
BEGIN;
ALTER TABLE post DROP CONSTRAINT IF EXISTS post_alert_lifecycle;
ALTER TABLE post ADD CONSTRAINT post_alert_lifecycle CHECK (
    (content_type IN ('urban_alert', 'safety_alert') AND expires_at IS NOT NULL AND expires_at > created_at)
    OR (content_type = 'publication' AND closed_at IS NULL AND (expires_at IS NULL OR expires_at > created_at))
    OR (content_type = 'event' AND expires_at IS NULL AND closed_at IS NULL)
);
COMMIT;

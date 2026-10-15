-- Événements fictifs de démonstration, lieux réels, coordonnées approximatives.
INSERT INTO post (id, user_id, content_type, title, description, location, latitude, longitude, starts_at, ends_at)
VALUES
('e0010000-0000-4000-8000-000000000001', 'strock-demo', 'event', 'Pique-nique des voisins au jardin',
 'Événement fictif de démonstration. Apportez votre lunch et une couverture pour rencontrer les voisins au jardin Jean-Paul-L’Allier. Gratuit et ouvert à tous.',
 'Jardin Jean-Paul-L’Allier, rue du Parvis, Québec', 46.8125, -71.2241,
 CURRENT_DATE + INTERVAL '2 days 16 hours', CURRENT_DATE + INTERVAL '2 days 18 hours'),
('e0010000-0000-4000-8000-000000000002', 'strock-demo', 'event', 'Échange de livres entre voisins',
 'Événement fictif de démonstration, sans affiliation avec la bibliothèque. Rendez-vous devant la bibliothèque Gabrielle-Roy avec un roman à échanger et vos suggestions de lecture.',
 'Bibliothèque Gabrielle-Roy, 350 rue Saint-Joseph Est, Québec', 46.8155, -71.2246,
 CURRENT_DATE + INTERVAL '3 days 14 hours', CURRENT_DATE + INTERVAL '3 days 16 hours'),
('e0010000-0000-4000-8000-000000000003', 'strock-demo', 'event', 'Balade photo dans Saint-Roch',
 'Événement fictif de démonstration. Départ du parvis de l’église Saint-Roch pour une promenade photo autour des façades et des murales du quartier. Un téléphone suffit !',
 'Parvis de l’église Saint-Roch, rue Saint-Joseph Est, Québec', 46.8165, -71.2231,
 CURRENT_DATE + INTERVAL '4 days 10 hours', CURRENT_DATE + INTERVAL '4 days 12 hours'),
('e0010000-0000-4000-8000-000000000004', 'strock-demo', 'event', 'Compétition de poutine chez Poutineville',
 'Événement fictif de démonstration. Qui composera la meilleure poutine de Saint-Roch ? Imaginez votre combinaison de frites, fromage et sauce, présentez votre création et votez pour votre favorite dans une compétition amicale chez Poutineville. Sans affiliation avec le restaurant.',
 'Poutineville Saint-Roch, 735 rue Saint-Joseph Est, Québec', 46.8177, -71.2206,
 CURRENT_DATE + INTERVAL '5 days 10 hours', CURRENT_DATE + INTERVAL '5 days 11 hours'),
('e0010000-0000-4000-8000-000000000005', 'strock-demo', 'event', 'Compétition d’art urbain',
 'Événement fictif de démonstration. Une compétition amicale d’art urbain devant la bibliothèque Gabrielle-Roy : créez une œuvre inspirée de Saint-Roch sur papier ou sur un panneau apporté pour l’occasion, puis participez au vote du public. Tous les styles sont bienvenus. Sans affiliation avec la bibliothèque.',
 'Bibliothèque Gabrielle-Roy, 350 rue Saint-Joseph Est, Québec', 46.8155, -71.2246,
 CURRENT_DATE + INTERVAL '6 days 14 hours', CURRENT_DATE + INTERVAL '6 days 16 hours')
ON CONFLICT (id) DO NOTHING;

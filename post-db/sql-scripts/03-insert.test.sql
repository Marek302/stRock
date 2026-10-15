\c "{{DB_NAME}}"

\echo 'Inserting into: {{DB_NAME}} ...'

\set comme_neuf_id '5c8a7b3c-9f13-485d-8b2a-2feed9a8e4a1'
\set acceptable_id 'a3359c1b-d8f7-4b2e-b4af-3d1e510bf9c9'
\set endommage_id '1b4e0f6a-6b5c-4fd7-9456-2b1f2ad2ef7d'

\set available_id '26fbcfa4-e63e-4666-8458-c544dff205c0'
\set sold_id '5735ce44-3b31-4058-8a1b-4c834c1fd984'
\set pending_id 'd6a25ebd-eb7f-43b0-a8a9-3a95ebb532ed'
\set draft_id 'd8a683fb-f74a-41ee-af5a-59bc574a7b15'

\set ship_id '1345bd31-fff5-489f-af26-1046f961a2ee'
\set local_meet_id '1ca8f728-8dc2-45a3-8243-30c2785f9a6d'
\set meet_at_university_id '2d60bda0-f220-4cf5-8ba2-42c162707abe'

INSERT INTO damage_state (id, name) VALUES 
(:'comme_neuf_id', 'Comme neuf'),
(:'acceptable_id', 'Acceptable'),
(:'endommage_id', 'Endommagé');

INSERT INTO sold_state (id, name) VALUES 
(:'available_id', 'Not Sold'),
(:'sold_id', 'Sold'),
(:'pending_id', 'Pending'),
(:'draft_id', 'Draft');

INSERT INTO shipping_offer (id, name, delivery_offer) VALUES 
(:'ship_id', 'Ship', TRUE),
(:'local_meet_id', 'Meet locally', FALSE),
(:'meet_at_university_id', 'Meet at university', FALSE);

-- Vendeurs: Sam Baribeault, Justin, Noa, Voisin Noa
-- book_categories: mock types for testing the recommendation ELO algorithm (aligned with onboarding options).
INSERT INTO listing (
    id, vendor_id, book_id, title, description, price,
    damage_state_id, sold_state_id, shipping_offer_id, location, is_annoted, seller_rep, buyer, book_categories
)
VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'kvG689qMNVequs7iLjWVIK6RUca2', 'kK8dMQAACAAJ', 'Calcul 1', 'Livre de calcul différentiel et intégral en excellent état.', 45.99, :'comme_neuf_id', :'available_id', :'ship_id', 'Montréal', FALSE, 5, NULL, ARRAY['Science', 'Technology']),
('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'kvG689qMNVequs7iLjWVIK6RUca2', '8yG8BAAAQBAJ', 'Chimie organique', 'Manuel de chimie organique avec quelques surlignages.', 52.50, :'acceptable_id', :'available_id', :'meet_at_university_id', 'Québec', FALSE, 4, NULL, ARRAY['Science']),
('c3d4e5f6-a7b8-9012-cdef-123456789012', 'kvG689qMNVequs7iLjWVIK6RUca2', 'Qy2lBAAAQBAJ', 'Physique mécanique', 'Couverture légèrement abîmée mais pages en bon état.', 38.00, :'acceptable_id', :'available_id', :'local_meet_id', 'Laval', FALSE, 3, NULL, ARRAY['Science', 'Technology']),
('d4e5f6a7-b8c9-0123-def1-234567890123', 'Y9SJv8HfDIehcvsNItQNb0Gj3A73', 'yGZ9DwAAQBAJ', 'Intro programmation', 'Introduction à la programmation en Python.', 35.00, :'comme_neuf_id', :'available_id', :'ship_id', 'Montréal', FALSE, 5, NULL, ARRAY['Technology', 'Science']),
('e5f6a7b8-c9d0-1234-ef12-345678901234', 'Y9SJv8HfDIehcvsNItQNb0Gj3A73', '3b9cDQAAQBAJ', 'Biologie cellulaire', 'Manuel de biologie avec schémas annotés.', 48.75, :'acceptable_id', :'sold_id', :'meet_at_university_id', 'Sherbrooke', FALSE, 4, 'kvG689qMNVequs7iLjWVIK6RUca2', ARRAY['Science']),
('f6a7b8c9-d0e1-2345-f123-456789012345', 'DUCMT9NpK1dp3A3JrrcjwZAs8Z83', 'u2q4BAAAQBAJ', 'Histoire du Québec', 'Livre d''histoire couvrant 1867-1980.', 28.50, :'acceptable_id', :'sold_id', :'local_meet_id', 'Gatineau', FALSE, 5, NULL, ARRAY['History']),
('a7b8c9d0-e1f2-3456-1234-567890123456', 'DUCMT9NpK1dp3A3JrrcjwZAs8Z83', '9sO4BAAAQBAJ', 'Algèbre linéaire', 'Manuel d''algèbre linéaire. État impeccable.', 42.00, :'comme_neuf_id', :'available_id', :'ship_id', 'Trois-Rivières', FALSE, 5, NULL, ARRAY['Science', 'Technology']),
('b8c9d0e1-f2a3-4567-2345-678901234567', '6GbNf8T7ZlcwbFMGs9p0oIn38Fi1', '5qK4BAAAQBAJ', 'Psycho développement', 'Introduction à la psychologie du développement.', 32.99, :'acceptable_id', :'pending_id', :'meet_at_university_id', 'Laval', FALSE, 3, NULL, ARRAY['Self-Help', 'Science']),
('c9d0e1f2-a3b4-5678-3456-789012345678', '6GbNf8T7ZlcwbFMGs9p0oIn38Fi1', '7rO4BAAAQBAJ', 'Microéconomie', 'Principes de microéconomie. Couverture usée.', 44.50, :'endommage_id', :'available_id', :'local_meet_id', 'Rimouski', FALSE, 2, NULL, ARRAY['Business', 'Science']),
('d0e1f2a3-b4c5-6789-4567-890123456789', '6GbNf8T7ZlcwbFMGs9p0oIn38Fi1', 'Xh8wAAAAYAAJ', 'Littérature québécoise', 'Recueil de textes littéraires québécois.', 29.99, :'comme_neuf_id', :'sold_id', :'ship_id', 'Sherbrooke', FALSE, 4, 'DUCMT9NpK1dp3A3JrrcjwZAs8Z83', ARRAY['Fiction']),
-- Deux annonces supplémentaires pour le vendeur DUCMT9NpK1dp3A3JrrcjwZAs8Z83
('e1f2a3b4-c5d6-4789-9abc-def012345678', 'DUCMT9NpK1dp3A3JrrcjwZAs8Z83', '1Q84BAAAQBAJ', 'Statistiques appliquées', 'Manuel de statistiques avec quelques exercices résolus.', 39.99, :'acceptable_id', :'available_id', :'ship_id', 'Montréal', FALSE, 5, NULL, ARRAY['Science', 'Technology']),
('f2a3b4c5-d6e7-489a-abcd-ef0123456789', 'DUCMT9NpK1dp3A3JrrcjwZAs8Z83', '2R95BAAAQBAJ', 'Analyse numérique', 'Livre d''analyse numérique, bon état général.', 41.50, :'comme_neuf_id', :'sold_id', :'local_meet_id', 'Québec', FALSE, 4, NULL, ARRAY['Science', 'Technology']);



INSERT INTO image (id, listing_id, image_index, image_path) VALUES
-- Listing 1
('516f02b6-52c4-4e48-8e4f-5ddee3024878', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 0, '/kvG689qMNVequs7iLjWVIK6RUca2/a1b2c3d4-e5f6-7890-abcd-ef1234567890/516f02b6-52c4-4e48-8e4f-5ddee3024878'),

-- Listing 2
('458ad951-6606-454b-8705-9b6cbc677d1f', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 0, '/kvG689qMNVequs7iLjWVIK6RUca2/b2c3d4e5-f6a7-8901-bcde-f12345678901/458ad951-6606-454b-8705-9b6cbc677d1f'),
('465fb85f-69c5-4bbc-957d-4ca4d70e442e', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 1, '/kvG689qMNVequs7iLjWVIK6RUca2/b2c3d4e5-f6a7-8901-bcde-f12345678901/465fb85f-69c5-4bbc-957d-4ca4d70e442e'),
('3fefb95c-6997-404a-9241-c46dbd1e261e', 'b2c3d4e5-f6a7-8901-bcde-f12345678901', 2, '/kvG689qMNVequs7iLjWVIK6RUca2/b2c3d4e5-f6a7-8901-bcde-f12345678901/3fefb95c-6997-404a-9241-c46dbd1e261e'),

-- Listing 3
('bfccafaf-7677-4f78-8966-350001f23e09', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 0, '/kvG689qMNVequs7iLjWVIK6RUca2/c3d4e5f6-a7b8-9012-cdef-123456789012/bfccafaf-7677-4f78-8966-350001f23e09'),
('201db779-ad47-4bdf-8d3f-28e2523b0f46', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 1, '/kvG689qMNVequs7iLjWVIK6RUca2/c3d4e5f6-a7b8-9012-cdef-123456789012/201db779-ad47-4bdf-8d3f-28e2523b0f46'),
('09aad376-42ae-4003-b9ef-fdef7e050a05', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 2, '/kvG689qMNVequs7iLjWVIK6RUca2/c3d4e5f6-a7b8-9012-cdef-123456789012/09aad376-42ae-4003-b9ef-fdef7e050a05'),
('1d90c096-43c3-4171-930b-a3fb3b390d46', 'c3d4e5f6-a7b8-9012-cdef-123456789012', 3, '/kvG689qMNVequs7iLjWVIK6RUca2/c3d4e5f6-a7b8-9012-cdef-123456789012/1d90c096-43c3-4171-930b-a3fb3b390d46'),

-- Listing 4
('cd852a09-d60d-4eb6-8067-49364aa939ef', 'd4e5f6a7-b8c9-0123-def1-234567890123', 0, '/Y9SJv8HfDIehcvsNItQNb0Gj3A73/d4e5f6a7-b8c9-0123-def1-234567890123/cd852a09-d60d-4eb6-8067-49364aa939ef'),
('e6ea201d-5833-4a40-a8f6-2bed7cc77ee3', 'd4e5f6a7-b8c9-0123-def1-234567890123', 1, '/Y9SJv8HfDIehcvsNItQNb0Gj3A73/d4e5f6a7-b8c9-0123-def1-234567890123/e6ea201d-5833-4a40-a8f6-2bed7cc77ee3'),
('948b08fb-0e40-4102-b212-a4356545a9b0', 'd4e5f6a7-b8c9-0123-def1-234567890123', 2, '/Y9SJv8HfDIehcvsNItQNb0Gj3A73/d4e5f6a7-b8c9-0123-def1-234567890123/948b08fb-0e40-4102-b212-a4356545a9b0'),

-- Listing 5
('dac03b4f-c98d-4704-870f-f43b16260225', 'e5f6a7b8-c9d0-1234-ef12-345678901234', 0, '/Y9SJv8HfDIehcvsNItQNb0Gj3A73/e5f6a7b8-c9d0-1234-ef12-345678901234/dac03b4f-c98d-4704-870f-f43b16260225'),
('a8b5a14f-7629-4cfe-98c5-4e1ff590c6e5', 'e5f6a7b8-c9d0-1234-ef12-345678901234', 1, '/Y9SJv8HfDIehcvsNItQNb0Gj3A73/e5f6a7b8-c9d0-1234-ef12-345678901234/a8b5a14f-7629-4cfe-98c5-4e1ff590c6e5'),
('ece1c58c-573c-4b60-b0f4-1719f0c7399b', 'e5f6a7b8-c9d0-1234-ef12-345678901234', 2, '/Y9SJv8HfDIehcvsNItQNb0Gj3A73/e5f6a7b8-c9d0-1234-ef12-345678901234/ece1c58c-573c-4b60-b0f4-1719f0c7399b'),

-- Listing 6
('ff0e7e8a-bf9e-4d13-ae72-1c7bff4697b7', 'f6a7b8c9-d0e1-2345-f123-456789012345', 1, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/f6a7b8c9-d0e1-2345-f123-456789012345/ff0e7e8a-bf9e-4d13-ae72-1c7bff4697b7'),
('e9c424cb-d4ae-4a20-83fe-0bf1176c6f3c', 'f6a7b8c9-d0e1-2345-f123-456789012345', 2, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/f6a7b8c9-d0e1-2345-f123-456789012345/e9c424cb-d4ae-4a20-83fe-0bf1176c6f3c'),
('31980186-252e-49d6-801b-8565b6c80bfc', 'f6a7b8c9-d0e1-2345-f123-456789012345', 3, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/f6a7b8c9-d0e1-2345-f123-456789012345/31980186-252e-49d6-801b-8565b6c80bfc'),

-- Listing 7
('c07d96ba-f295-43e8-848d-718c1565367e', 'a7b8c9d0-e1f2-3456-1234-567890123456', 1, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/a7b8c9d0-e1f2-3456-1234-567890123456/c07d96ba-f295-43e8-848d-718c1565367e'),
('ce8f5536-f9c8-4fee-bc91-8b9c82c17873', 'a7b8c9d0-e1f2-3456-1234-567890123456', 2, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/a7b8c9d0-e1f2-3456-1234-567890123456/ce8f5536-f9c8-4fee-bc91-8b9c82c17873'),

-- Listing 8
('e6474911-0a74-4dd3-9d58-fc66fb250fca', 'b8c9d0e1-f2a3-4567-2345-678901234567', 1, '/6GbNf8T7ZlcwbFMGs9p0oIn38Fi1/b8c9d0e1-f2a3-4567-2345-678901234567/e6474911-0a74-4dd3-9d58-fc66fb250fca'),
('b458284a-f0f3-4907-9263-45035b97b963', 'b8c9d0e1-f2a3-4567-2345-678901234567', 2, '/6GbNf8T7ZlcwbFMGs9p0oIn38Fi1/b8c9d0e1-f2a3-4567-2345-678901234567/b458284a-f0f3-4907-9263-45035b97b963'),

-- Listing 9
('1afd2d35-1ea3-4e6c-b875-a5b2e619d8e6', 'c9d0e1f2-a3b4-5678-3456-789012345678', 1, '/6GbNf8T7ZlcwbFMGs9p0oIn38Fi1/c9d0e1f2-a3b4-5678-3456-789012345678/1afd2d35-1ea3-4e6c-b875-a5b2e619d8e6'),
('7f77ac9b-1639-4d4b-af6e-d8721e5d3afc', 'c9d0e1f2-a3b4-5678-3456-789012345678', 2, '/6GbNf8T7ZlcwbFMGs9p0oIn38Fi1/c9d0e1f2-a3b4-5678-3456-789012345678/7f77ac9b-1639-4d4b-af6e-d8721e5d3afc'),

-- Listing 10
('91a0513c-24bb-4e4a-ab9e-f95f2cd244c3', 'd0e1f2a3-b4c5-6789-4567-890123456789', 1, '/6GbNf8T7ZlcwbFMGs9p0oIn38Fi1/d0e1f2a3-b4c5-6789-4567-890123456789/91a0513c-24bb-4e4a-ab9e-f95f2cd244c3'),

-- Listing 11 (Statistiques appliquées)
('a1e2f3b4-c5d6-4789-9abc-def012345679', 'e1f2a3b4-c5d6-4789-9abc-def012345678', 0, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/e1f2a3b4-c5d6-4789-9abc-def012345678/a1e2f3b4-c5d6-4789-9abc-def012345679'),

-- Listing 12 (Analyse numérique)
('b2f3a4c5-d6e7-489a-abcd-ef0123456780', 'f2a3b4c5-d6e7-489a-abcd-ef0123456789', 0, '/DUCMT9NpK1dp3A3JrrcjwZAs8Z83/f2a3b4c5-d6e7-489a-abcd-ef0123456789/b2f3a4c5-d6e7-489a-abcd-ef0123456780');

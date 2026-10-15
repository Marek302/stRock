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

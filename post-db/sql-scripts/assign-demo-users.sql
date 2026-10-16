-- Répartition des cinq publications fictives uniquement. Réexécutable.
UPDATE post AS p SET user_id = demo.user_id
FROM (VALUES
  ('e0010000-0000-4000-8000-000000000001'::uuid, 'strock-demo-alice'),
  ('e0010000-0000-4000-8000-000000000002'::uuid, 'strock-demo-karim'),
  ('e0010000-0000-4000-8000-000000000003'::uuid, 'strock-demo-lea'),
  ('e0010000-0000-4000-8000-000000000004'::uuid, 'strock-demo-alice'),
  ('e0010000-0000-4000-8000-000000000005'::uuid, 'strock-demo-karim')
) AS demo(post_id, user_id)
WHERE p.id = demo.post_id;

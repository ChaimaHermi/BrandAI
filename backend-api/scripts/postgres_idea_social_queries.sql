-- Requêtes PostgreSQL équivalentes à la migration Alembic s1t2u3v4w5x6
-- (à utiliser seulement si vous migrez à la main sans Alembic ; sinon : alembic upgrade head)

-- 1) Supprimer l’ancienne contrainte « une connexion par utilisateur et provider »
ALTER TABLE user_social_connections DROP CONSTRAINT IF EXISTS uq_user_social_provider;

-- 2) Colonne + FK + index
ALTER TABLE user_social_connections ADD COLUMN IF NOT EXISTS idea_id INTEGER REFERENCES ideas(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_user_social_connections_idea_id ON user_social_connections(idea_id);

-- 3) Rattacher chaque ligne à la dernière idée du même utilisateur
UPDATE user_social_connections u
SET idea_id = (
  SELECT i.id FROM ideas i
  WHERE i.user_id = u.user_id
  ORDER BY i.created_at DESC NULLS LAST, i.id DESC
  LIMIT 1
)
WHERE EXISTS (SELECT 1 FROM ideas i2 WHERE i2.user_id = u.user_id);

-- 4) Supprimer les connexions sans idée (utilisateur sans projet)
DELETE FROM user_social_connections WHERE idea_id IS NULL;

-- 5) Dupliquer les jetons sur les autres idées du même utilisateur
INSERT INTO user_social_connections (
  user_id, idea_id, provider, payload_encrypted,
  account_name, page_name, facebook_url, instagram_url, linkedin_url,
  created_at, updated_at
)
SELECT
  u.user_id,
  i.id,
  u.provider,
  u.payload_encrypted,
  u.account_name,
  u.page_name,
  u.facebook_url,
  u.instagram_url,
  u.linkedin_url,
  u.created_at,
  u.updated_at
FROM ideas i
INNER JOIN user_social_connections u ON u.user_id = i.user_id
WHERE u.idea_id IS NOT NULL
  AND i.id <> u.idea_id
  AND NOT EXISTS (
    SELECT 1 FROM user_social_connections x
    WHERE x.idea_id = i.id AND x.provider = u.provider
  );

-- 6) NOT NULL + unicité par idée
ALTER TABLE user_social_connections ALTER COLUMN idea_id SET NOT NULL;
ALTER TABLE user_social_connections ADD CONSTRAINT uq_idea_social_provider UNIQUE (idea_id, provider);

-- Vérification rapide
-- SELECT idea_id, provider, COUNT(*) FROM user_social_connections GROUP BY 1,2 HAVING COUNT(*) > 1;

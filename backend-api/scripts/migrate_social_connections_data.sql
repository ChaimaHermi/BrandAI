-- =============================================================================
-- Migration manuelle / audit : user_social_connections → social_connections
-- =============================================================================
-- La migration Alembic officielle est : t1u2v3w4x5y6_social_connections_table_refactor
--   cd backend-api && alembic upgrade head
--
-- Ce script documente la cible et des requêtes utiles APRÈS migration.
-- Il ne doit PAS être exécuté sur une base déjà migrée sans adaptation.
-- =============================================================================

-- Plateformes attendues (une ligne par compte) :
--   facebook_page        — payload JSON complet Meta (user_access_token, pages, selected_page_id)
--   instagram_business   — { page_id, page_access_token, instagram_business_account_id? }
--   linkedin             — { access_token, person_urn, name }

-- Vérifier l’absence de doublons par idée + plateforme :
-- SELECT idea_id, platform, COUNT(*) FROM social_connections GROUP BY 1, 2 HAVING COUNT(*) > 1;

-- Lister les connexions par idée :
-- SELECT id, idea_id, platform, platform_account_id, profile_url, token_expires_at, account_name, page_name
-- FROM social_connections ORDER BY idea_id, platform;

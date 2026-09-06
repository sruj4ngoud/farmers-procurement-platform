-- Demo staff/admin accounts only.
-- Farmer rows are imported from CSV in Phase 3. Do not duplicate that dataset here.
-- password_hash is a placeholder until authentication is implemented.
-- centre_id is left NULL until centres are imported.

INSERT INTO users (username, password_hash, role, is_active)
VALUES
    ('centre.staff', 'PHASE2_PLACEHOLDER_HASH', 'CENTRE_STAFF', TRUE),
    ('admin', 'PHASE2_PLACEHOLDER_HASH', 'ADMIN', TRUE)
ON CONFLICT (username) DO NOTHING;

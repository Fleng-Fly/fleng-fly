\set ON_ERROR_STOP on
-- Session-only settings; no system configuration is changed.
SET password_encryption = 'scram-sha-256';
SELECT version();
-- Refuse to repurpose an existing privileged account as an application role.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fleng'
               AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
        RAISE EXCEPTION 'Existing fleng role has elevated privileges; manual review required';
    END IF;
END $$;
SELECT 'CREATE ROLE fleng LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fleng')
\gexec
ALTER ROLE fleng LOGIN;
-- psql encrypts the password before sending it; prompts have echo disabled.
\password fleng
SELECT 'CREATE DATABASE fleng_db OWNER fleng'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'fleng_db')
\gexec
-- Do not change ownership of an unexpected existing database automatically.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'fleng_db'
               AND pg_get_userbyid(datdba) <> 'fleng') THEN
        RAISE EXCEPTION 'Existing fleng_db is owned by another role; manual review required';
    END IF;
END $$;
SELECT rolname, rolcanlogin, NOT rolsuper AS no_superuser,
       rolpassword LIKE 'SCRAM-SHA-256$%' AS scram_password
FROM pg_authid WHERE rolname = 'fleng';
SELECT datname, pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname = 'fleng_db';
SELECT type, database, user_name, address, auth_method, error
FROM pg_hba_file_rules ORDER BY rule_number;

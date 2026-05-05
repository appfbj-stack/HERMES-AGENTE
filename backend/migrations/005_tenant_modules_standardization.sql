ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS whatsapp_evolution BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS followup BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE tenant_modules
SET whatsapp_evolution = whatsapp
WHERE whatsapp_evolution IS DISTINCT FROM whatsapp;

UPDATE tenant_modules
SET followup = crm
WHERE followup IS DISTINCT FROM crm;

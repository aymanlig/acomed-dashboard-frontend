create database if not exist acomed ;  
use acomed ;  
CREATE TABLE utilisateurs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    nom VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL, -- Hashed
    role role_type NOT NULL,
    region VARCHAR(100),
    -- خاصين بـ المفتش
    matricule VARCHAR(50) UNIQUE,
    zone_assignee VARCHAR(100),
    disponible BOOLEAN DEFAULT true,
    -- خاصين بـ الإدمين
    niveau_acces INT,
    departement VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE etablissements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom VARCHAR(255) NOT NULL,
    type etab_type NOT NULL,
    region VARCHAR(100) NOT NULL,
    adresse TEXT,
    contact VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE missions_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_debut DATE NOT NULL,
    date_fin DATE,
    statut statut_mission DEFAULT 'PLANIFIEE',
    inspecteur_id UUID REFERENCES utilisateurs(id) ON DELETE SET NULL,
    etablissement_id UUID REFERENCES etablissements(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE formulaires_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID REFERENCES missions_audit(id) ON DELETE CASCADE,
    categorie VARCHAR(100) NOT NULL,
    reponses JSONB NOT NULL, -- JSONB حسن من JSON العادي فـ Postgres
    synced BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    formulaire_id UUID REFERENCES formulaires_audit(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    gravite niveau_gravite NOT NULL,
    statut VARCHAR(50) DEFAULT 'NOUVEAU',
    date_signalement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE actions_correctives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    etablissement_id UUID REFERENCES etablissements(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    deadline DATE NOT NULL,
    statut statut_action DEFAULT 'OUVERTE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--1 hada dyalna 7na 
CREATE ROLE admin_role WITH SUPERUSER LOGIN PASSWORD '1234';

-- hada dyal muftich 
CREATE ROLE inspecteur_role WITH LOGIN PASSWORD '1234';

-- hada li ayder dak analys li glty lia
CREATE ROLE python_analyst_role WITH LOGIN PASSWORD '1234';

-GRANT SELECT ON formulaires_audit TO python_analyst_role;

GRANT SELECT, INSERT, UPDATE ON formulaires_audit TO inspecteur_role;
CREATE TABLE historique_modifications (
    id SERIAL PRIMARY KEY,
    nom_table VARCHAR(50),
    action VARCHAR(10), -- واش INSERT ولا UPDATE
    utilisateur VARCHAR(50), -- شكون دارها
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- فوقاش دارها
    donnees_anciennes JSONB, -- الداتا القديمة قبل التعديل
    donnees_nouvelles JSONB -- الداتا الجديدة
);


CREATE OR REPLACE FUNCTION enregistrer_historique()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        INSERT INTO historique_modifications (nom_table, action, utilisateur, donnees_anciennes, donnees_nouvelles)
        VALUES (TG_TABLE_NAME, 'UPDATE', current_user, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO historique_modifications (nom_table, action, utilisateur, donnees_nouvelles)
        VALUES (TG_TABLE_NAME, 'INSERT', current_user, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trigger_audit_formulaires
AFTER INSERT OR UPDATE ON formulaires_audit
FOR EACH ROW EXECUTE FUNCTION enregistrer_historique();
CREATE INDEX idx_formulaires_reponses ON formulaires_audit USING GIN (reponses); 
 






 
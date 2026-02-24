-- ============================================================
-- DataFoundation: MySQL Staging Schema
-- Healthcare Provider Analytics Repository
-- ============================================================

CREATE DATABASE IF NOT EXISTS healthcare_staging;
USE healthcare_staging;

-- -----------------------------------------------------------
-- Staging: Providers
-- -----------------------------------------------------------
DROP TABLE IF EXISTS stg_procedures;
DROP TABLE IF EXISTS stg_conditions;
DROP TABLE IF EXISTS stg_encounters;
DROP TABLE IF EXISTS stg_patients;
DROP TABLE IF EXISTS stg_providers;
DROP TABLE IF EXISTS stg_organizations;
DROP TABLE IF EXISTS stg_hospital_readmissions;

CREATE TABLE stg_providers (
    provider_id     VARCHAR(36) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    gender          CHAR(1),
    speciality      VARCHAR(100),
    organization    VARCHAR(200),
    city            VARCHAR(100),
    state           VARCHAR(2),
    zip             VARCHAR(10),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- Staging: Patients
-- -----------------------------------------------------------
CREATE TABLE stg_patients (
    patient_id      VARCHAR(36) PRIMARY KEY,
    birthdate       DATE,
    deathdate       DATE,
    first_name      VARCHAR(50),
    last_name       VARCHAR(50),
    gender          CHAR(1),
    race            VARCHAR(20),
    ethnicity       VARCHAR(20),
    city            VARCHAR(100),
    state           VARCHAR(50),
    zip             VARCHAR(10),
    marital_status  CHAR(1),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- Staging: Encounters
-- -----------------------------------------------------------
CREATE TABLE stg_encounters (
    encounter_id        VARCHAR(36) PRIMARY KEY,
    patient_id          VARCHAR(36),
    provider_id         VARCHAR(36),
    encounter_type      VARCHAR(50),
    encounter_class     VARCHAR(50),
    start_datetime      DATETIME,
    end_datetime        DATETIME,
    total_cost          DECIMAL(12, 2),
    reason_code         VARCHAR(20),
    reason_description  VARCHAR(200),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES stg_patients(patient_id),
    FOREIGN KEY (provider_id) REFERENCES stg_providers(provider_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- Staging: Conditions
-- -----------------------------------------------------------
CREATE TABLE stg_conditions (
    condition_id    VARCHAR(36) PRIMARY KEY,
    patient_id      VARCHAR(36),
    encounter_id    VARCHAR(36),
    code            VARCHAR(20),
    description     VARCHAR(200),
    onset_date      DATE,
    abatement_date  DATE NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES stg_patients(patient_id),
    FOREIGN KEY (encounter_id) REFERENCES stg_encounters(encounter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- Staging: Procedures
-- -----------------------------------------------------------
CREATE TABLE stg_procedures (
    procedure_id        VARCHAR(36) PRIMARY KEY,
    patient_id          VARCHAR(36),
    encounter_id        VARCHAR(36),
    code                VARCHAR(20),
    description         VARCHAR(200),
    performed_datetime  DATETIME,
    cost                DECIMAL(12, 2),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES stg_patients(patient_id),
    FOREIGN KEY (encounter_id) REFERENCES stg_encounters(encounter_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- Staging: CMS Hospital Readmissions
-- -----------------------------------------------------------
CREATE TABLE stg_hospital_readmissions (
    id                          INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id                 VARCHAR(20),
    hospital_name               VARCHAR(200),
    measure_name                VARCHAR(100),
    number_of_discharges        INT,
    expected_readmission_rate   DECIMAL(8, 4),
    predicted_readmission_rate  DECIMAL(8, 4),
    excess_readmission_ratio    DECIMAL(8, 4),
    number_of_readmissions      INT,
    start_date                  DATE,
    end_date                    DATE,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------
-- Indexes for query performance
-- -----------------------------------------------------------
CREATE INDEX idx_encounters_patient ON stg_encounters(patient_id);
CREATE INDEX idx_encounters_provider ON stg_encounters(provider_id);
CREATE INDEX idx_encounters_type ON stg_encounters(encounter_type);
CREATE INDEX idx_encounters_start ON stg_encounters(start_datetime);
CREATE INDEX idx_conditions_patient ON stg_conditions(patient_id);
CREATE INDEX idx_conditions_code ON stg_conditions(code);
CREATE INDEX idx_procedures_patient ON stg_procedures(patient_id);
CREATE INDEX idx_readmissions_hospital ON stg_hospital_readmissions(hospital_id);
CREATE INDEX idx_readmissions_measure ON stg_hospital_readmissions(measure_name);
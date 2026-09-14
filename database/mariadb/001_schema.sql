-- AreaData MariaDB 10.6 baseline. Run in the dedicated areadata database.
-- Source files and large GeoJSON/Parquet assets stay outside this database;
-- their immutable hashes and paths are recorded here.
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dataset_version (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  dataset_code VARCHAR(32) NOT NULL,
  version_label VARCHAR(64) NOT NULL,
  schema_version VARCHAR(16) NOT NULL,
  generated_at DATETIME(6) NOT NULL,
  content_sha256 CHAR(64) NOT NULL,
  status VARCHAR(24) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_dataset_version (dataset_code, version_label),
  UNIQUE KEY uq_dataset_hash (dataset_code, content_sha256),
  CONSTRAINT chk_dataset_status CHECK (status IN ('staging','validated','published','superseded','failed'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS source_record (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  source_key VARCHAR(160) NOT NULL,
  name VARCHAR(500) NOT NULL,
  publisher VARCHAR(500) NULL,
  url TEXT NULL,
  status VARCHAR(32) NOT NULL,
  retrieved_at DATETIME(6) NULL,
  reference_period VARCHAR(255) NULL,
  license_text TEXT NULL,
  content_sha256 CHAR(64) NULL,
  raw_asset_path TEXT NULL,
  note TEXT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_source_key (source_key),
  KEY ix_source_status (status),
  CONSTRAINT chk_source_status CHECK (status IN ('ready','partial','missing','not_collected','not_available','failed','unverified'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS geography (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  dataset_version_id BIGINT UNSIGNED NOT NULL,
  geography_key VARCHAR(190) NOT NULL,
  name VARCHAR(500) NOT NULL,
  level_key VARCHAR(80) NOT NULL,
  type_key VARCHAR(80) NOT NULL,
  country_iso3 CHAR(3) NULL,
  official_code VARCHAR(160) NULL,
  code_system VARCHAR(255) NULL,
  boundary_version VARCHAR(255) NULL,
  source_id BIGINT UNSIGNED NULL,
  valid_from DATE NULL,
  valid_to DATE NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_geography_version_key (dataset_version_id, geography_key),
  KEY ix_geography_country_level (dataset_version_id, country_iso3, level_key),
  KEY ix_geography_code (code_system, official_code),
  CONSTRAINT fk_geography_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_version(id),
  CONSTRAINT fk_geography_source FOREIGN KEY (source_id) REFERENCES source_record(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS geography_membership (
  dataset_version_id BIGINT UNSIGNED NOT NULL,
  parent_geography_id BIGINT UNSIGNED NOT NULL,
  child_geography_id BIGINT UNSIGNED NOT NULL,
  position_no INT UNSIGNED NOT NULL DEFAULT 0,
  membership_source_id BIGINT UNSIGNED NOT NULL,
  membership_set_key VARCHAR(190) NOT NULL,
  membership_set_complete TINYINT(1) NOT NULL DEFAULT 0,
  valid_from DATE NULL,
  valid_to DATE NULL,
  PRIMARY KEY (dataset_version_id, parent_geography_id, child_geography_id, membership_set_key),
  KEY ix_membership_child (dataset_version_id, child_geography_id),
  CONSTRAINT fk_membership_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_version(id),
  CONSTRAINT fk_membership_parent FOREIGN KEY (parent_geography_id) REFERENCES geography(id),
  CONSTRAINT fk_membership_child FOREIGN KEY (child_geography_id) REFERENCES geography(id),
  CONSTRAINT fk_membership_source FOREIGN KEY (membership_source_id) REFERENCES source_record(id),
  CONSTRAINT chk_no_self_membership CHECK (parent_geography_id <> child_geography_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS indicator (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  indicator_key VARCHAR(190) NOT NULL,
  name VARCHAR(500) NOT NULL,
  theme VARCHAR(190) NOT NULL,
  definition TEXT NULL,
  definition_key VARCHAR(190) NULL,
  unit VARCHAR(160) NOT NULL,
  population_scope VARCHAR(500) NULL,
  measurement_method VARCHAR(255) NULL,
  aggregation_method VARCHAR(32) NOT NULL DEFAULT 'official_only',
  source_id BIGINT UNSIGNED NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_indicator_key (indicator_key),
  CONSTRAINT fk_indicator_source FOREIGN KEY (source_id) REFERENCES source_record(id),
  CONSTRAINT chk_indicator_aggregation CHECK (aggregation_method IN ('none','official_only','sum','ratio','weighted_mean'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS observation (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  dataset_version_id BIGINT UNSIGNED NOT NULL,
  geography_id BIGINT UNSIGNED NOT NULL,
  indicator_id BIGINT UNSIGNED NOT NULL,
  period_label VARCHAR(80) NOT NULL,
  period_start DATE NULL,
  period_end DATE NULL,
  numeric_value DECIMAL(32,10) NULL,
  value_status VARCHAR(32) NOT NULL,
  source_id BIGINT UNSIGNED NOT NULL,
  dimensions_json JSON NULL,
  dimensions_sha256 CHAR(64) NOT NULL DEFAULT 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  definition_override TEXT NULL,
  unit_override VARCHAR(160) NULL,
  population_override VARCHAR(500) NULL,
  method_override VARCHAR(255) NULL,
  boundary_version VARCHAR(255) NULL,
  footnote TEXT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_observation_identity (dataset_version_id, geography_id, indicator_id, period_label, dimensions_sha256),
  KEY ix_observation_query (dataset_version_id, indicator_id, period_label, geography_id),
  KEY ix_observation_geography (dataset_version_id, geography_id, period_label),
  CONSTRAINT fk_observation_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_version(id),
  CONSTRAINT fk_observation_geography FOREIGN KEY (geography_id) REFERENCES geography(id),
  CONSTRAINT fk_observation_indicator FOREIGN KEY (indicator_id) REFERENCES indicator(id),
  CONSTRAINT fk_observation_source FOREIGN KEY (source_id) REFERENCES source_record(id),
  CONSTRAINT chk_observation_status CHECK (value_status IN ('observed','missing','not_collected','not_available','not_applicable','unverified','failed')),
  CONSTRAINT chk_observation_value CHECK ((value_status='observed' AND numeric_value IS NOT NULL) OR (value_status<>'observed' AND numeric_value IS NULL)),
  CONSTRAINT chk_dimensions_json CHECK (dimensions_json IS NULL OR JSON_VALID(dimensions_json))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aggregation_rule (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  indicator_id BIGINT UNSIGNED NOT NULL,
  method VARCHAR(32) NOT NULL,
  completeness_policy VARCHAR(32) NOT NULL,
  period_policy VARCHAR(48) NOT NULL DEFAULT 'same_period',
  numerator_indicator_id BIGINT UNSIGNED NULL,
  denominator_indicator_id BIGINT UNSIGNED NULL,
  weight_indicator_id BIGINT UNSIGNED NULL,
  label VARCHAR(500) NOT NULL,
  note TEXT NOT NULL,
  active TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_aggregation_indicator (indicator_id),
  CONSTRAINT fk_aggregation_indicator FOREIGN KEY (indicator_id) REFERENCES indicator(id),
  CONSTRAINT fk_aggregation_numerator FOREIGN KEY (numerator_indicator_id) REFERENCES indicator(id),
  CONSTRAINT fk_aggregation_denominator FOREIGN KEY (denominator_indicator_id) REFERENCES indicator(id),
  CONSTRAINT fk_aggregation_weight FOREIGN KEY (weight_indicator_id) REFERENCES indicator(id),
  CONSTRAINT chk_aggregation_method CHECK (method IN ('sum','ratio','weighted_mean')),
  CONSTRAINT chk_aggregation_completeness CHECK (completeness_policy='full_cover'),
  CONSTRAINT chk_aggregation_period CHECK (period_policy IN ('same_period','latest_available_by_component'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aggregate_result (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  dataset_version_id BIGINT UNSIGNED NOT NULL,
  target_geography_id BIGINT UNSIGNED NOT NULL,
  indicator_id BIGINT UNSIGNED NOT NULL,
  period_label VARCHAR(80) NOT NULL,
  result_status VARCHAR(32) NOT NULL,
  numeric_value DECIMAL(32,10) NULL,
  covered_subtotal DECIMAL(32,10) NULL,
  component_count INT UNSIGNED NOT NULL DEFAULT 0,
  missing_count INT UNSIGNED NOT NULL DEFAULT 0,
  inputs_sha256 CHAR(64) NOT NULL,
  calculated_at DATETIME(6) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_aggregate_result (dataset_version_id, target_geography_id, indicator_id, period_label, inputs_sha256),
  CONSTRAINT fk_result_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_version(id),
  CONSTRAINT fk_result_geography FOREIGN KEY (target_geography_id) REFERENCES geography(id),
  CONSTRAINT fk_result_indicator FOREIGN KEY (indicator_id) REFERENCES indicator(id),
  CONSTRAINT chk_result_status CHECK (result_status IN ('calculated','incomplete','incomparable')),
  CONSTRAINT chk_result_value CHECK ((result_status='calculated' AND numeric_value IS NOT NULL AND missing_count=0) OR (result_status<>'calculated' AND numeric_value IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aggregate_component (
  aggregate_result_id BIGINT UNSIGNED NOT NULL,
  component_geography_id BIGINT UNSIGNED NOT NULL,
  observation_id BIGINT UNSIGNED NOT NULL,
  component_value DECIMAL(32,10) NOT NULL,
  PRIMARY KEY (aggregate_result_id, component_geography_id),
  CONSTRAINT fk_component_result FOREIGN KEY (aggregate_result_id) REFERENCES aggregate_result(id) ON DELETE CASCADE,
  CONSTRAINT fk_component_geography FOREIGN KEY (component_geography_id) REFERENCES geography(id),
  CONSTRAINT fk_component_observation FOREIGN KEY (observation_id) REFERENCES observation(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS boundary_asset (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  dataset_version_id BIGINT UNSIGNED NOT NULL,
  geography_id BIGINT UNSIGNED NOT NULL,
  source_id BIGINT UNSIGNED NOT NULL,
  geometry_edition VARCHAR(255) NOT NULL,
  asset_path TEXT NOT NULL,
  asset_sha256 CHAR(64) NOT NULL,
  min_lon DECIMAL(10,7) NULL,
  min_lat DECIMAL(10,7) NULL,
  max_lon DECIMAL(10,7) NULL,
  max_lat DECIMAL(10,7) NULL,
  reference_only TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uq_boundary_identity (dataset_version_id, geography_id, geometry_edition),
  CONSTRAINT fk_boundary_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_version(id),
  CONSTRAINT fk_boundary_geography FOREIGN KEY (geography_id) REFERENCES geography(id),
  CONSTRAINT fk_boundary_source FOREIGN KEY (source_id) REFERENCES source_record(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

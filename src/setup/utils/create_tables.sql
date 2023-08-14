CREATE SCHEMA IF NOT EXISTS bhr
    AUTHORIZATION postgres;

-- Create main tables
CREATE TABLE IF NOT EXISTS bhr.companies
(
    id uuid NOT NULL,
    company_name text COLLATE pg_catalog."default" NOT NULL,
    career_site_url text COLLATE pg_catalog."default",
    ats text COLLATE pg_catalog."default",
    CONSTRAINT companies_pkey PRIMARY KEY (id),
    CONSTRAINT companies_unique UNIQUE (company_name)
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.companies
    OWNER to postgres;

CREATE TABLE IF NOT EXISTS bhr.jobs
(
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    title text COLLATE pg_catalog."default" NOT NULL,
    url text COLLATE pg_catalog."default" NOT NULL,
    description text COLLATE pg_catalog."default",
    salary text COLLATE pg_catalog."default",
    location text COLLATE pg_catalog."default",
    active boolean,
    new boolean,
    insert_timestamp timestamp without time zone NOT NULL,
    scrape_insert_run_id uuid NOT NULL,
    scrape_inactive_run_id uuid,
    remote boolean,
    searchable_description tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, description)) STORED,
    CONSTRAINT jobs_pkey PRIMARY KEY (id),
    CONSTRAINT jobs_fkey_companies FOREIGN KEY (company_id)
        REFERENCES bhr.companies (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.jobs
    OWNER to postgres;
CREATE INDEX IF NOT EXISTS fki_jobs_fkey_companies
    ON bhr.jobs USING btree
    (company_id ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS ts_searchable_description_idx
    ON bhr.jobs USING gin
    (searchable_description)
    TABLESPACE pg_default;

-- Create location tables
CREATE TABLE IF NOT EXISTS bhr.countries
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    name text COLLATE pg_catalog."default" NOT NULL,
    code character(2) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT countries_pkey PRIMARY KEY (id),
    CONSTRAINT countries_unique UNIQUE (name, code)
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.countries
    OWNER to postgres;

CREATE TABLE IF NOT EXISTS bhr.country_divisions
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    country_id integer NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default",
    CONSTRAINT country_divisions_pkey PRIMARY KEY (id),
    CONSTRAINT country_divisions_unique UNIQUE (country_id, name),
    CONSTRAINT country_divisions_fkey FOREIGN KEY (country_id)
        REFERENCES bhr.countries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.country_divisions
    OWNER to postgres;

CREATE TABLE IF NOT EXISTS bhr.cities
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    country_id integer NOT NULL,
    country_division_id integer NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    latitude text COLLATE pg_catalog."default" NOT NULL,
    longitude text COLLATE pg_catalog."default" NOT NULL,
    timezone text COLLATE pg_catalog."default" NOT NULL,
    population integer NOT NULL,
    CONSTRAINT cities_pkey PRIMARY KEY (id),
    CONSTRAINT cities_unique UNIQUE (country_id, country_division_id, name, latitude, longitude),
    CONSTRAINT cities_countries_fkey FOREIGN KEY (country_id)
        REFERENCES bhr.countries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT cities_country_divisions_fkey FOREIGN KEY (country_division_id)
        REFERENCES bhr.country_divisions (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.cities
    OWNER to postgres;

CREATE TABLE IF NOT EXISTS bhr.locations
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    country_id integer NOT NULL,
    country_division_id integer,
    city_id bigint,
    location text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT normalized_locations_pkey PRIMARY KEY (id),
    CONSTRAINT normalized_locations_unique_location UNIQUE NULLS NOT DISTINCT (country_id, country_division_id, city_id),
    CONSTRAINT normalized_locations_fkey_cities FOREIGN KEY (city_id)
        REFERENCES bhr.cities (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT normalized_locations_fkey_countries FOREIGN KEY (country_id)
        REFERENCES bhr.countries (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT normalized_locations_fkey_country_divisions FOREIGN KEY (country_division_id)
        REFERENCES bhr.country_divisions (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.locations
    OWNER to postgres;

CREATE TABLE IF NOT EXISTS bhr.jobs_locations
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    job_id uuid,
    location_id bigint,
    location text COLLATE pg_catalog."default",
    CONSTRAINT job_locations_pkey PRIMARY KEY (id),
    CONSTRAINT job_locations_unique_job_location UNIQUE NULLS NOT DISTINCT (job_id, location_id),
    CONSTRAINT job_locations_fkey_jobs FOREIGN KEY (job_id)
        REFERENCES bhr.jobs (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT job_locations_fkey_locations FOREIGN KEY (location_id)
        REFERENCES bhr.locations (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
TABLESPACE pg_default;
ALTER TABLE IF EXISTS bhr.jobs_locations
    OWNER to postgres;
CREATE INDEX IF NOT EXISTS fki_job_locations_fkey_jobs
    ON bhr.jobs_locations USING btree
    (job_id ASC NULLS LAST)
    TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS fki_job_locations_fkey_locations
    ON bhr.jobs_locations USING btree
    (location_id ASC NULLS LAST)
    TABLESPACE pg_default;


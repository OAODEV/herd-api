-- Created by Vertabelo (http://vertabelo.com)
-- Last modification date: 2016-04-01 17:50:23.624


-- added by jesse.miller@adops.com
-- modified by thomas.yager-madden@adops.com

-- must be database superuser to CREATE EXTENSION;
-- we should find some other way to do this — I suggest manually for now.
-- CREATE EXTENSION hstore;

-- wrap schema change in a transaction, so everything either works or fails atomically
BEGIN;

-- tables
-- Table: branch
CREATE TABLE branch (
    branch_id serial  NOT NULL,
    service_id int  NOT NULL,
    branch_name varchar(100)  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    CONSTRAINT branch_name_service_id UNIQUE (branch_name, service_id) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT branch_pk PRIMARY KEY (branch_id)
);



-- Table: config
CREATE TABLE config (
    config_id serial  NOT NULL,
    key_value_pairs hstore  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    CONSTRAINT key_value_pairs UNIQUE (key_value_pairs) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT config_pk PRIMARY KEY (config_id)
);



-- Table: iteration
CREATE TABLE iteration (
    iteration_id serial  NOT NULL,
    branch_id int  NOT NULL,
    commit_hash varchar(100)  NOT NULL,
    image_name varchar(100)  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    CONSTRAINT branch_id_commit_hash UNIQUE (branch_id, commit_hash) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT iteration_pk PRIMARY KEY (iteration_id)
);



-- Table: release
CREATE TABLE release (
    release_id serial  NOT NULL,
    iteration_id int  NOT NULL,
    config_id int  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    service_version_seq int  NOT NULL,
    branch_version_seq int  NOT NULL,
    CONSTRAINT release_pk PRIMARY KEY (release_id)
);

-- added by thomas.yager-madden@adops.com
-- Trigger function on 'release'
CREATE OR REPLACE FUNCTION increment_version() RETURNS TRIGGER AS $version$
    DECLARE
        service_seq integer;
        branch_seq integer;
    BEGIN
        SELECT COALESCE(max(service_version_seq), 0)
          FROM release
          JOIN iteration USING (iteration_id)
          JOIN branch USING (branch_id)
          JOIN service USING (service_id)
         WHERE iteration_id = NEW.iteration_id
         GROUP BY service_id
          INTO service_seq;

        SELECT COALESCE(max(branch_version_seq), 0)
          FROM release
          JOIN iteration USING (iteration_id)
          JOIN branch USING (branch_id)
         WHERE iteration_id = NEW.iteration_id
         GROUP BY branch_id
          INTO branch_seq;

        service_seq := service_seq + 1;
        branch_seq := branch_seq + 1;

        UPDATE release SET service_version_seq = service_seq
                         , branch_version_seq = branch_seq
         WHERE release_id = NEW.release_id;
        return NEW;
    END;
$version$ LANGUAGE plpgsql;

CREATE TRIGGER release_version_increment_trig
AFTER INSERT ON release
FOR EACH ROW EXECUTE PROCEDURE increment_version();


-- Table: service
CREATE TABLE service (
    service_id serial  NOT NULL,
    service_name varchar(100)  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    CONSTRAINT service_name UNIQUE (service_name) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT service_pk PRIMARY KEY (service_id)
);







-- foreign keys
-- Reference:  branch_service (table: branch)

ALTER TABLE branch ADD CONSTRAINT branch_service
    FOREIGN KEY (service_id)
    REFERENCES service (service_id)
    NOT DEFERRABLE
    INITIALLY IMMEDIATE
;

-- Reference:  iteration_branch (table: iteration)

ALTER TABLE iteration ADD CONSTRAINT iteration_branch
    FOREIGN KEY (branch_id)
    REFERENCES branch (branch_id)
    NOT DEFERRABLE
    INITIALLY IMMEDIATE
;

-- Reference:  release_config (table: release)

ALTER TABLE release ADD CONSTRAINT release_config
    FOREIGN KEY (config_id)
    REFERENCES config (config_id)
    NOT DEFERRABLE
    INITIALLY IMMEDIATE
;

-- Reference:  release_iteration (table: release)

ALTER TABLE release ADD CONSTRAINT release_iteration
    FOREIGN KEY (iteration_id)
    REFERENCES iteration (iteration_id)
    NOT DEFERRABLE
    INITIALLY IMMEDIATE
;

-- commit our wrapper transaction
COMMIT;


-- End of file.

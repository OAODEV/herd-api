-- Created by Vertabelo (http://vertabelo.com)
-- Last modification date: 2016-05-09 21:33:00.182

CREATE EXTENSION hstore;

-- tables
-- Table: branch
CREATE TABLE branch (
    branch_id serial  NOT NULL,
    service_id int  NOT NULL,
    branch_name varchar(100)  NOT NULL,
    merge_base_commit_hash varchar(100)  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    deleted_dt timestamp  NOT NULL DEFAULT 'infinity',
    CONSTRAINT branch_name_merge_base_deleted_dt UNIQUE (branch_name, merge_base_commit_hash, deleted_dt) NOT DEFERRABLE  INITIALLY IMMEDIATE,
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
    service_version_seq int  NOT NULL DEFAULT 0,
    branch_version_seq int  NOT NULL DEFAULT 0,
    CONSTRAINT release_pk PRIMARY KEY (release_id)
);

create or replace function increment_version() returns trigger as $version$
    declare
        service_seq integer;
        branch_seq integer;
    begin
        select coalesce(max(service_version_seq), 0)
          from release
          join iteration using (iteration_id)
          join branch using (branch_id)
          join service using (service_id)
         where iteration_id = NEW.iteration_id
         group by service_id
          into service_seq;

        select coalesce(max(branch_version_seq), 0)
          from release
          join iteration using (iteration_id)
          join branch using (branch_id)
         where iteration_id = NEW.iteration_id
         group by branch_id
          into branch_seq;

        service_seq := service_seq + 1;
        branch_seq := branch_seq + 1;

        update release set service_version_seq = service_seq
                         , branch_version_seq = branch_seq
         where release_id = NEW.release_id;
        return NEW;
    end;
$version$ language plpgsql;

create trigger release_version_increment_trig
after insert on release
for each row execute procedure increment_version();;

-- Table: service
CREATE TABLE service (
    service_id serial  NOT NULL,
    service_name varchar(100)  NOT NULL,
    created_dt timestamp  NOT NULL DEFAULT now(),
    CONSTRAINT service_name UNIQUE (service_name) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT service_pk PRIMARY KEY (service_id)
);

-- foreign keys
-- Reference: branch_service (table: branch)
ALTER TABLE branch ADD CONSTRAINT branch_service
    FOREIGN KEY (service_id)
    REFERENCES service (service_id)  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: iteration_branch (table: iteration)
ALTER TABLE iteration ADD CONSTRAINT iteration_branch
    FOREIGN KEY (branch_id)
    REFERENCES branch (branch_id)  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: release_config (table: release)
ALTER TABLE release ADD CONSTRAINT release_config
    FOREIGN KEY (config_id)
    REFERENCES config (config_id)  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: release_iteration (table: release)
ALTER TABLE release ADD CONSTRAINT release_iteration
    FOREIGN KEY (iteration_id)
    REFERENCES iteration (iteration_id)  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- End of file.


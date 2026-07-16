-- BlueCrystal database bootstrap v1_5_13
-- Client: Navicat or any PostgreSQL SQL client
-- Execute once while connected to an existing maintenance database, normally postgres.
-- PostgreSQL does not support CREATE DATABASE IF NOT EXISTS.
-- If bluecrystal already exists, do not execute this file again.
-- The database owner defaults to the role executing CREATE DATABASE.

CREATE DATABASE bluecrystal
    WITH
    ENCODING = 'UTF8'
    TEMPLATE = template0;

-- BlueWhale database bootstrap v1_5_3
-- Client: Navicat or any PostgreSQL SQL client
-- Execute once while connected to an existing maintenance database, normally postgres.
-- PostgreSQL does not support CREATE DATABASE IF NOT EXISTS.
-- If bluewhale already exists, do not execute this file again.
-- The database owner defaults to the role executing CREATE DATABASE.

CREATE DATABASE bluewhale
    WITH
    ENCODING = 'UTF8'
    TEMPLATE = template0;

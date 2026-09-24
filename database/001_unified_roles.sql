-- Run once on the existing mathsy_db before starting the standardized build.
USE mathsy_db;
ALTER TABLE users MODIFY role ENUM('student','teacher','parent','admin') NOT NULL;


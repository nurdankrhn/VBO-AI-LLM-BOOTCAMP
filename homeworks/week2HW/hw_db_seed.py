from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.getenv("PG_DSN"))

with engine.begin() as conn:

    conn.execute(text("""
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS departments;
    """))

    conn.execute(text("""
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            location VARCHAR(100) NOT NULL
        );
    """))

    conn.execute(text("""
        CREATE TABLE employees (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            department_id INTEGER NOT NULL REFERENCES departments(id),
            salary INTEGER NOT NULL,
            country VARCHAR(50) NOT NULL
        );
    """))

    conn.execute(text("""
        INSERT INTO departments(name, location)
        VALUES
        ('Engineering','New York'),
        ('Marketing','Toronto'),
        ('Finance','London');
    """))

    conn.execute(text("""
        INSERT INTO employees(full_name, department_id, salary, country)
        VALUES
        ('John Smith',1,120000,'USA'),
        ('David Brown',1,150000,'USA'),
        ('Emily Davis',2,80000,'Canada'),
        ('Michael Johnson',3,95000,'UK');
    """))

print("Database seeded.")
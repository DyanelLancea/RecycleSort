# **Alembic & Database Guide**

This document explains how our team should manage database schema changes using **Alembic**. It covers how to apply migrations, generate new ones, and recover the database if the SQLite file is deleted.

---

## **1. Overview**

We use **SQLAlchemy** for models and **Alembic** for schema migrations.  
Alembic ensures every teammate has the same database structure without manually creating tables.

- **SQLite** is our local development database.
- **Alembic** manages all schema changes.
- **Never modify tables manually** — always use migrations.

---
## **Important! Run Alembic from the ROOT project folder (RecycleSort Folder)**
Do not cd to src folder when you run the backend or Alembic. 

Remain in the **RecycleSort folder** and run:
```
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 43181
```

If you see import errors such as:
- ModuleNotFoundError: No module named 'app'
- ModuleNotFoundError: No module named 'src'
This might mean Python cannot locate the src folder in its module search path.

Step 1. Check your python module path:
```
python -c "import sys; print(sys.path)"
```

Look for path ending with  .../RecycleSort/src folder.

If not, add project root src folder to PYTHONPATH. 
1. Open windows environment varaibles
2. Under user variables click New. 
3. Add
- Varaible name: PYTHONPATH
- Variable value: <file path to RecycleSort/src folder>

---

## **2. Applying Migrations (Required After Every Pull)**

Whenever you pull new code that includes schema changes, run:

```
alembic upgrade head
```

This updates your local database to the latest schema version.

If you skip this step, you may see errors like:

- “Database not up to date”
- Missing columns or tables
- Health check failing

---

## **3. Generating a New Migration (When You Change Models)**

If you add or modify a column/table in SQLAlchemy models, generate a migration:

```
alembic revision --autogenerate -m "describe your change"
```

Then apply it:

```
alembic upgrade head
```

Finally, **commit the migration file** so the team stays in sync.

---

## **4. If Your SQLite Database File Is Deleted**

Deleting the `.sqlite3` file removes:

- all tables  
- all schema  
- all data  

To recreate the schema:

```
alembic upgrade head
```

This restores **all tables and columns**, including the latest changes (e.g., `image_filename`).  
It does **not** restore data.

---

## **5. Migration Files Must Be Committed**

Every migration file inside:

```
migrations/versions/
```

must be committed to Git.

This ensures:

- everyone has the same schema history  
- Alembic can apply migrations consistently  
- no teammate gets “database not up to date” errors  

Never delete or rename migration files unless the team agrees.

---

## **6. Do Not Manually Create or Edit Tables**

Avoid:

- creating tables by hand  
- altering columns manually  
- editing the SQLite file directly  

All schema changes must go through Alembic.

Manual edits cause schema drift and break migrations.

---

## **7. Checking Migration Status**

To see your current migration version:

```
alembic current
```

To see full migration history:

```
alembic history
```

---

## **8. Common Issues & Fixes**

### **Issue:** “Database not up to date”  
**Fix:**  
Run:

```
alembic upgrade head
```

### **Issue:** Missing column after pulling code  
**Fix:**  
Run:

```
alembic upgrade head
```

### **Issue:** Deleted `.sqlite3` file  
**Fix:**  
Recreate schema:

```
alembic upgrade head
```

---

## **9. Summary**

- Run `alembic upgrade head` after every pull.  
- Generate migrations when you change models.  
- Commit migration files.  
- Alembic restores schema, not data.  
- Never manually edit tables.

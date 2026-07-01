# Arquitectura — Baby Milk Tracker

```mermaid
graph TD
    subgraph Cliente
        B[Navegador / PWA]
    end

    subgraph Render["Render (web service)"]
        G[Gunicorn]
        W[web.py\nrutas Flask]
        subgraph Módulos["baby_milk_tracker/"]
            AU[auth.py\nlogin / registro]
            DB[database.py\ninit tablas]
            MG[migrations.py\nalter table]
            MO[models.py\ndataclasses]
            ST[storage.py\nSQL CRUD]
            PC[percentiles.py\ncurvas OMS]
            TU[time_utils.py\ntimezone AR]
        end
        T[templates/\nJinja2 HTML]
        S[static/\nCSS · icons · PWA]
    end

    subgraph BaseDatos["Base de datos"]
        SQ[SQLite\ndesarrollo local]
        PG[Supabase PostgreSQL\nproducción]
    end

    B -- HTTP --> G
    G --> W
    W --> AU
    W --> ST
    W --> PC
    W --> TU
    W --> T
    ST --> DB
    ST --> MO
    DB --> MG
    ST -- DATABASE_URL ausente --> SQ
    ST -- DATABASE_URL definida --> PG
    T --> B
    S --> B
```

## Flujo de una request típica

```
Navegador
   │  GET /
   ▼
Gunicorn → web.py (index route)
   │  get_user_settings(user_id)
   │  get_last_feeding(baby_id)
   │  get_last_growth_record(baby_id)
   │  get_next_appointment(baby_id)
   ▼
storage.py → SQL query
   ▼
SQLite (local) / PostgreSQL Supabase (producción)
   │
   ▼
web.py → render_template("index.html", ...)
   ▼
Navegador recibe HTML renderizado
```

## Estructura de la base de datos

```
users ──────────────┐
  id PK             │
  username          │ (user_id FK)
  password_hash     │
                    ▼
               babies
                 id PK
                 user_id FK
                 first_name
                 last_name
                 birth_date
                 sex
                    │
         ┌──────────┼──────────┬──────────────┬───────────────┐
         ▼          ▼          ▼              ▼               ▼
     feedings   pumpings  growth_records  appointments  medical_studies
     (baby_id)  (baby_id)   (baby_id)      (baby_id)     (baby_id)

                    │ (user_id FK)
                    ▼
              user_settings
              (show_pumpings)
```

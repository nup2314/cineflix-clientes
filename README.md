# 🎬 CineFlix - Registro de clientes

Flask + PostgreSQL (Neon), listo para desplegar en Render. Este repositorio contiene solo esta app.

## 1. Base de datos (Neon)
1. Crea un proyecto en https://neon.tech.
2. Copia la cadena de conexión (termina en `?sslmode=require`).
3. Las tablas se crean solas al arrancar.

## 2. GitHub
Crea un repositorio vacío y, dentro de esta carpeta:

```bash
git init
git add .
git commit -m "CineFlix clientes"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/cineflix-clientes.git
git push -u origin main
```

`app.py` debe quedar en la raíz del repositorio. No subas tu archivo `.env` (el `.gitignore` ya lo evita).

## 3. Render
New + → **Web Service** → elige el repositorio y usa:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Variables de entorno:
  - `DATABASE_URL`: la cadena de Neon
  - `ADMIN_PASSWORD`: una contraseña larga
  - `ADMIN_USER`: admin
  - `SECRET_KEY`: una cadena larga y aleatoria
  - `PYTHON_VERSION`: 3.12.7

(O usa New + → Blueprint, que lee `render.yaml` y te pide solo DATABASE_URL y ADMIN_PASSWORD.)

## Probar en tu computadora
```bash
cp .env.example .env     # Windows: copy .env.example .env
# edita .env con tus datos
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000/
```

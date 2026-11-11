"""CineFlix - Registro de clientes (Flask + PostgreSQL en Neon)."""
import hmac
import os
import re
import time
from datetime import date
from functools import wraps

from dotenv import load_dotenv

load_dotenv()  # Lee el archivo .env cuando trabajas en tu computadora.

import psycopg2
import psycopg2.extras
from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Render define la variable RENDER; allí la cookie solo viaja por HTTPS.
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
)
CSRFProtect(app)

DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------ BASE DE DATOS
def get_conn():
    """Abre una conexión con PostgreSQL (Neon)."""
    if not DATABASE_URL:
        raise RuntimeError("Falta la variable de entorno DATABASE_URL.")
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=15,
    )


def db(sql, params=(), fetch=None):
    """Ejecuta una instrucción SQL y confirma (commit) los cambios."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch == "all":
                    return cur.fetchall()
                if fetch == "one":
                    return cur.fetchone()
    finally:
        conn.close()


def init_db():
    """Crea la tabla si todavía no existe."""
    db("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            telefono TEXT NOT NULL,
            fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE
        )
    """)


init_db()


# ------------------------------------------------------------------- SESIÓN
def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get("autenticado"):
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltura


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("autenticado"):
        return redirect(url_for("clientes"))

    error = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        correcto = bool(
            ADMIN_PASSWORD
            and hmac.compare_digest(usuario.encode(), ADMIN_USER.encode())
            and hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
        )
        if correcto:
            session.clear()
            session["autenticado"] = True
            return redirect(url_for("clientes"))
        time.sleep(1)  # frena los intentos de adivinar la contraseña
        error = "Usuario o contraseña incorrectos."

    return render_template("login.html", errores=[error] if error else [])


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------------------------------------------------------- CLIENTES
@app.route("/", methods=["GET", "POST"])
@login_required
def clientes():
    errores = []
    form_data = {}

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = re.sub(r"[\s\-()]", "", request.form.get("telefono", ""))
        form_data = request.form

        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not EMAIL_RE.match(correo):
            errores.append("Escribe un correo electrónico válido.")
        if not (telefono.isdigit() and len(telefono) == 10):
            errores.append("El teléfono debe tener 10 dígitos.")

        if not errores:
            try:
                db("""
                    INSERT INTO clientes (nombre, correo, telefono)
                    VALUES (%s, %s, %s)
                """, (nombre, correo, telefono))
            except psycopg2.IntegrityError:
                errores.append("Ya existe un cliente con ese correo.")
            else:
                flash("¡Cliente registrado correctamente!", "success")
                return redirect(url_for("clientes"))

    lista = db("SELECT * FROM clientes ORDER BY id DESC", fetch="all")
    return render_template(
        "clientes.html", clientes=lista, errores=errores, form_data=form_data
    )


@app.route("/eliminar/<int:cliente_id>", methods=["POST"])
@login_required
def eliminar_cliente(cliente_id):
    db("DELETE FROM clientes WHERE id = %s", (cliente_id,))
    flash("El cliente fue eliminado.", "info")
    return redirect(url_for("clientes"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)

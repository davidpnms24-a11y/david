from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
import hashlib
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__)
app.secret_key = 'tiburones'

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'cineplus1')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

mysql = MySQL(app)

def VerificarToken():

    if 'token' not in session:
        return False

    token = session['token']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT dExpira
        FROM token
        WHERE cToken=%s
        ORDER BY idToken DESC
        LIMIT 1
        """,
        [token]
    )

    registro = cursor.fetchone()

    cursor.close()

    if registro is None:
        return False

    fecha_expira = registro[0]

    if datetime.now() > fecha_expira:
        return False

    return True

def VerificarToken():

    if 'token' not in session:
        return False

    token = session['token']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT dExpira
        FROM token
        WHERE cToken=%s
        ORDER BY idToken DESC
        LIMIT 1
        """,
        [token]
    )

    registro = cursor.fetchone()

    cursor.close()

    if registro is None:
        return False

    fecha_expira = registro[0]

    if datetime.now() > fecha_expira:
        return False

    return True

def ActualizarToken():

    if 'token' not in session:
        return

    token = session['token']

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT minutosToken FROM configuracion LIMIT 1"
    )

    configuracion = cursor.fetchone()

    minutos = configuracion[0]

    nueva_expiracion = datetime.now() + timedelta(minutes=minutos)

    cursor.execute(
        """
        UPDATE token
        SET dExpira=%s
        WHERE cToken=%s
        """,
        (
            nueva_expiracion,
            token
        )
    )

    mysql.connection.commit()

    cursor.close()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/validar', methods=['POST'])
def validar():

    usuario = request.form['usuario']
    clave = request.form['clave']

    clave_md5 = hashlib.md5(clave.encode()).hexdigest()

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM usuario WHERE cUsuario=%s AND cClave=%s",
        (usuario, clave_md5)
    )

    cuenta = cursor.fetchone()

    if cuenta:

        # Obtener duración del token
        cursor.execute(
            "SELECT minutosToken FROM configuracion LIMIT 1"
        )

        configuracion = cursor.fetchone()

        minutos = configuracion[0]

        # Generar fechas
        fecha_actual = datetime.now()

        fecha_expira = fecha_actual + timedelta(minutes=minutos)

        # Generar token único
        token = str(uuid.uuid4())

        # Guardar token en la tabla token
        cursor.execute(
            """
            INSERT INTO token
            (idUsuario,cToken,dFecha,dExpira)
            VALUES(%s,%s,%s,%s)
            """,
            (
                cuenta[0],
                token,
                fecha_actual,
                fecha_expira
            )
        )

        mysql.connection.commit()

        session['loggedin'] = True
        session['usuario'] = usuario
        session['token'] = token

        cursor.close()

        return redirect(url_for('dashboard'))

    else:

        cursor.close()

        return "Usuario o contraseña incorrectos"

@app.route('/dashboard')
def dashboard():

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if not VerificarToken():

        session.clear()

        return redirect(url_for('login'))

    ActualizarToken()

    return render_template('dashboard.html')

@app.route('/salir')
def salir():

    session.pop('loggedin', None)
    session.pop('usuario', None)
    session.pop('token', None)

    return redirect(url_for('login'))

@app.route('/usuarios')
def usuarios():

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if not VerificarToken():

        session.clear()

        return redirect(url_for('login'))
    ActualizarToken()

    cursor = mysql.connection.cursor()

    cursor.execute("SELECT idUsuario,cUsuario FROM usuario")

    usuarios = cursor.fetchall()

    cursor.close()

    return render_template(
        'usuarios.html',
        usuarios=usuarios
    )
@app.route('/peliculas')
def peliculas():

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if not VerificarToken():

        session.clear()

        return redirect(url_for('login'))
    ActualizarToken()

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT idPelicula,cTitulo,cGenero FROM pelicula"
    )

    peliculas = cursor.fetchall()

    cursor.close()

    return render_template(
        'peliculas.html',
        peliculas=peliculas
    )

@app.route('/configuracion')
def configuracion():

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if not VerificarToken():

        session.clear()

        return redirect(url_for('login'))
    ActualizarToken()

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM configuracion"
    )

    configuracion = cursor.fetchone()

    cursor.close()

    return render_template(
        'configuracion.html',
        configuracion=configuracion
    )

@app.route('/guardar_usuario', methods=['POST'])
def guardar_usuario():

    usuario = request.form['usuario']
    clave = request.form['clave']

    clave_md5 = hashlib.md5(clave.encode()).hexdigest()

    cursor = mysql.connection.cursor()

    cursor.execute(
        "INSERT INTO usuario(cUsuario,cClave) VALUES(%s,%s)",
        (usuario, clave_md5)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/usuarios')

@app.route('/eliminar_usuario/<id>')
def eliminar_usuario(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM usuario WHERE idUsuario=%s",
        [id]
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/usuarios')

@app.route('/EditarUsuario/<id>')
def EditarUsuario(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM usuario WHERE idUsuario=%s",
        [id]
    )

    usuario = cursor.fetchone()

    cursor.close()

    return render_template(
        'EditarUsuario.html',
        usuario=usuario
    )

@app.route('/ActualizarUsuario', methods=['POST'])
def ActualizarUsuario():

    id = request.form['id']
    usuario = request.form['usuario']
    clave = request.form['clave']

    clave_md5 = hashlib.md5(clave.encode()).hexdigest()

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE usuario
        SET cUsuario=%s,
            cClave=%s
        WHERE idUsuario=%s
        """,
        (usuario, clave_md5, id)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/usuarios')

@app.route('/GuardarPelicula', methods=['POST'])
def GuardarPelicula():

    titulo = request.form['titulo']
    genero = request.form['genero']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO pelicula(cTitulo,cGenero)
        VALUES(%s,%s)
        """,
        (titulo, genero)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/peliculas')

@app.route('/EliminarPelicula/<id>')
def EliminarPelicula(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM pelicula WHERE idPelicula=%s",
        [id]
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/peliculas')

@app.route('/EditarPelicula/<id>')
def EditarPelicula(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM pelicula WHERE idPelicula=%s",
        [id]
    )

    pelicula = cursor.fetchone()

    cursor.close()

    return render_template(
        'EditarPelicula.html',
        pelicula=pelicula
    )

@app.route('/ActualizarPelicula', methods=['POST'])
def ActualizarPelicula():

    id = request.form['id']
    titulo = request.form['titulo']
    genero = request.form['genero']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE pelicula
        SET cTitulo=%s,
            cGenero=%s
        WHERE idPelicula=%s
        """,
        (titulo, genero, id)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/peliculas')

@app.route('/catalogo')
def catalogo():

    busqueda = request.args.get('busqueda', '')

    cursor = mysql.connection.cursor()

    if busqueda:

        cursor.execute(
            """
            SELECT idPelicula, cTitulo, cGenero
            FROM pelicula
            WHERE cTitulo LIKE %s
            """,
            ('%' + busqueda + '%',)
        )

    else:

        cursor.execute(
            """
            SELECT idPelicula, cTitulo, cGenero
            FROM pelicula
            """
        )

    peliculas = cursor.fetchall()

    cursor.close()

    return render_template(
        'catalogo.html',
        peliculas=peliculas,
        busqueda=busqueda
    )

@app.route('/detalle_pelicula/<int:id>')
def detalle_pelicula(id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT idPelicula, cTitulo, cGenero
        FROM pelicula
        WHERE idPelicula=%s
        """,
        (id,)
    )

    pelicula = cursor.fetchone()

    cursor.close()

    if pelicula is None:
        return "Película no encontrada", 404

    return render_template(
        'DetallePelicula.html',
        pelicula=pelicula
    )

@app.route('/ActualizarConfiguracion', methods=['POST'])
def ActualizarConfiguracion():

    id = request.form['id']
    minutos = request.form['minutos']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE configuracion
        SET minutosToken=%s
        WHERE idConfiguracion=%s
        """,
        (minutos, id)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect('/configuracion')

@app.route('/generos')
def generos():
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM genero")
    generos = cursor.fetchall()
    cursor.close()

    return render_template('generos.html', generos=generos)


@app.route('/guardar_genero', methods=['POST'])
def guardar_genero():
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    nombre = request.form['nombre']

    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO genero (nombre) VALUES (%s)",
        (nombre,)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('generos'))


@app.route('/EditarGenero/<int:id>')
def editar_genero(id):
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT * FROM genero WHERE id = %s",
        (id,)
    )
    genero = cursor.fetchone()
    cursor.close()

    return render_template('EditarGenero.html', genero=genero)


@app.route('/ActualizarGenero', methods=['POST'])
def actualizar_genero():
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    id = request.form['id']
    nombre = request.form['nombre']

    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE genero SET nombre = %s WHERE id = %s",
        (nombre, id)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('generos'))


@app.route('/EliminarGenero/<int:id>')
def eliminar_genero(id):
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        "DELETE FROM genero WHERE id = %s",
        (id,)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('generos'))

@app.route('/categorias')
def categorias():
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM categoria")
    categorias = cursor.fetchall()
    cursor.close()

    return render_template('categorias.html', categorias=categorias)


@app.route('/guardar_categoria', methods=['POST'])
def guardar_categoria():
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    nombre = request.form['nombre']

    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO categoria (nombre) VALUES (%s)",
        (nombre,)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('categorias'))


@app.route('/EditarCategoria/<int:id>')
def editar_categoria(id):
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT * FROM categoria WHERE id = %s",
        (id,)
    )
    categoria = cursor.fetchone()
    cursor.close()

    return render_template(
        'EditarCategoria.html',
        categoria=categoria
    )


@app.route('/ActualizarCategoria', methods=['POST'])
def actualizar_categoria():
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    id = request.form['id']
    nombre = request.form['nombre']

    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE categoria SET nombre = %s WHERE id = %s",
        (nombre, id)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('categorias'))


@app.route('/EliminarCategoria/<int:id>')
def eliminar_categoria(id):
    if not VerificarToken():
        session.clear()
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        "DELETE FROM categoria WHERE id = %s",
        (id,)
    )
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('categorias'))

if __name__ == '__main__':
    app.run(debug=True)
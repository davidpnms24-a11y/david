from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
import hashlib
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = 'tiburones'

app.config['MYSQL_HOST'] = 'sql5.freesqldatabase.com'
app.config['MYSQL_USER'] = 'sql5833321'
app.config['MYSQL_PASSWORD'] = 'ICkMjZYVr1'
app.config['MYSQL_DB'] = 'sql5833321'
app.config['MYSQL_PORT'] = 3306

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

if __name__ == '__main__':
    app.run(debug=True)
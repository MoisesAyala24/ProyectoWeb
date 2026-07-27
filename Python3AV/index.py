from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL 
import hashlib 
import secrets
from datetime import datetime


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'tiendaupp'

mysql = MySQL(app)

app.secret_key = 'Tiburones'


@app.before_request
def verificar_sesion():

 if 'usuario' in session:

     ahora = datetime.now().timestamp()

     ultima = session.get('ultima_actividad')

     if ultima:

       if ahora - ultima > 300:

         cur = mysql.connection.cursor()

         cur.execute("""
           DELETE FROM token
           WHERE Idusuario=%s
         """,(session['usuario'],))


         mysql.connection.commit()
         session.clear()
         return redirect('/login')
     session['ultima_actividad'] = ahora


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/validar-login', methods=['POST'])
def validar_login():

    correo = request.form['correo']
    password = request.form['password']

    password = hashlib.md5(password.encode()).hexdigest()

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT *
        FROM usuario
        WHERE correo=%s
        AND contraseña=%s
    """, (correo, password))

    user = cur.fetchone()

    if user:
        token = secrets.token_hex(32)
        session['usuario'] = user[0]
        session['nombre'] = user[1]
        session['token'] = token
        session['ultima_actividad'] = datetime.now().timestamp()
        cur.execute("""
            INSERT INTO token(Idusuario,token)
            VALUES(%s,%s)
        """,(user[0],token))
        mysql.connection.commit()
        return redirect('/usuario')

    return " Usuario o contraseña incorrectos"


@app.route('/usuario')
def usuario():

    if 'usuario' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT * FROM usuario
        WHERE idusuario=%s
    """, (session['usuario'],))

    data = cur.fetchone()

    return render_template('usuario.html', user=data)


@app.route('/logout')
def logout():
    if 'usuario' in session:
       cur = mysql.connection.cursor()
       cur.execute("""
          DELETE FROM token
          WHERE Idusuario=%s
       """,(session['usuario'],))
       mysql.connection.commit()
    session.clear()
    return redirect('/login')


@app.route('/registro')
def registro():
    return render_template('registro.html')


@app.route('/registrar-usuario', methods=['POST'])
def registrar_usuario():

    nombre = request.form['nombre']
    correo = request.form['correo']
    password = request.form['password']
    password = hashlib.md5(password.encode()).hexdigest()

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM usuario WHERE correo=%s", (correo,))
    existe = cur.fetchone()

    if existe:
        return "El usuario ya existe"

    cur.execute("""
        INSERT INTO usuario (nombre, correo, contraseña)
        VALUES (%s, %s, %s)
    """, (nombre, correo, password))

    mysql.connection.commit()

    return redirect('/login')


@app.route('/productos')
def productos():

    if 'usuario' not in session:
        return redirect('/login')

    return render_template('productos.html')


@app.route('/agregar')
def agregar():
    return render_template('agregar.html')


@app.route('/insertar-producto', methods=['POST'])
def insertar_producto():

    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO producto (cNombre, cDescripcion, iPrecio, cFoto, LActivo)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, descripcion, precio, 'default.png', 1))

    mysql.connection.commit()

    return redirect('/productos')


@app.route('/editar-producto/<int:id>')
def editar_producto(id):

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM producto WHERE id = %s", (id,))
    data = cur.fetchone()

    return render_template('editar-producto.html', producto=data)


@app.route('/actualizar-producto/<int:id>', methods=['POST'])
def actualizar_producto(id):

    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE producto
        SET cNombre=%s, cDescripcion=%s, iPrecio=%s
        WHERE id=%s
    """, (nombre, descripcion, precio, id))

    mysql.connection.commit()

    return redirect('/productos')


@app.route('/borrar-producto/<int:id>')
def borrar_producto(id):

    cur = mysql.connection.cursor()
    cur.execute("UPDATE producto SET LActivo=0 WHERE id=%s", (id,))
    mysql.connection.commit()

    return redirect('/productos')


@app.route('/clientes')
def clientes():

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM producto WHERE lActivo=1")
    data = cur.fetchall()

    return render_template('clientes.html', Clientes=data)


if __name__ == '__main__':
    app.run(port=3000, debug=True)
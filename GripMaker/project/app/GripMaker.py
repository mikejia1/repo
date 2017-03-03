__author__ = 'admin-u5515287'
import os
from random import randint
from stl import mesh
from flask import Flask, render_template, request, flash, send_from_directory
from flask_wtf import FlaskForm
from wtforms import DecimalField, RadioField, SubmitField

app = Flask(__name__)
app.secret_key = 'mikeys_secret_key'
TEMP = 'temp/'

file_dict = {
    'A': 'ls_hex_grip.stl',
    'B': 'ls_hybrid_grip.stl',
    'C': 'ls_spacer_grip.stl',
    'D': 'b_round_grip.stl',
    'E': 'b_hex_grip.stl',
    'F': 'sh_round_grip.stl'
}

# Slot tolerance (w1, w3, t)
slot_dict = {
    'A': (25, 15, 7.5),
    'B': (25, 15, 7.5),
    'C': (25, 14, 7),
    'D': (25, 15, 7.5),
    'E': (25, 15, 7.5),
    'F': (25, 15, 6),
}

class GripMakerForm(FlaskForm):
    g = DecimalField("g: grip length")
    w1 = DecimalField("w1: width of slot at base of the grip")
    w2 = DecimalField("w2: width of the slot half way through the grip")
    w3 = DecimalField("w3: width of the slot at the top of the grip")
    t = DecimalField("t: tang thickness")
    choice = RadioField("Grip choice", choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F')])
    submit = SubmitField("submit")


@app.route('/make_grip', methods=['POST'])
def make_grip():
    clear_dir()
    form = GripMakerForm()
    # Load stl file:
    grip = mesh.Mesh.from_file("stl/" + file_dict[form.choice.data])

    # Edit mesh
    w1 = float(form.w1.data) + 0.2
    w2 = float(form.w2.data) + 0.2
    w3 = float(form.w3.data) + 0.2
    t  = float(form.t.data) + 0.2
    g  = float(form.g.data)

    a = (w2/2 - linear_x(w1, w3, 50, 100))/(square_x(w1, w3, 50, 100)-linear_x(w1, w3, 50, 100))
    if a < 0:
        a = 0
    b = 1 - a

    tol = slot_dict[form.choice.data]
    if a > 1 or w1 < w2 or w1 < w3 or w2 < w3:
        return render_template('oops.html')

    # Scale the grip if tang dimensions are too large
    scalef = (max(w1/tol[0] if w1 > tol[0] else 1, w3/tol[1] if w3 > tol[1] else 1), t/tol[2] if t > tol[2] else 1)
    scaled = scalef[0] != 1 or scalef[1] != 1

    for idx, face in enumerate(grip.data["vectors"]):
        for vector in face:
            # Scale grip length
            if form.choice.data == 'C':
                if vector[2] < 48.5:  # Lower grip
                    vector[2] *= (g-14)/86
                elif vector[2] < 61.5:  # Spacer inset
                    vector[2] += 48 * (g-14)/86 - 48
                else:
                    vector[2] = ((g-14)/86)*(vector[2] - 14) + 14
            else:
                vector[2] *= g/100

            if abs(round(vector[0])) == 1 and abs(round(vector[1])) == 1:
                z = round(vector[2])
                # Set tang dimensions
                x = a*square_x(w1, w3, z, g) + b*linear_x(w1, w3, z, g)
                vector[0] *= x
                vector[1] *= t/2
            else:
                # Scale grip
                vector[0] *= scalef[0]
                vector[1] *= scalef[1]

    file_name = str(randint(0, 10000)) + '.stl'
    filepath = TEMP + file_name
    grip.save(filepath)
    return send_from_directory(TEMP, file_name, as_attachment=True, attachment_filename=file_dict[form.choice.data])


def clear_dir():
    try:
        for item in os.listdir(TEMP):
            os.unlink(TEMP + item)
    except Exception as error:
        print"Error removing or closing downloaded file handle:", error.strerror


def square_x(w1, w3, z, g):
    return ((w1-w3)/2)*(g**2-z**2)/g**2 + w3/2


def linear_x(w1, w3, z, g):
    return w1/2 - (w1-w3)*z/(g*2)


@app.route('/', methods=['GET', 'POST'])
def home():
    form = GripMakerForm()
    if request.method == 'POST':
        if not form.validate():
            flash('All fields are required.')
            return render_template("gripmaker.html", form=form)
        else:
            return make_grip(form)
    elif request.method == 'GET':
        return render_template("gripmaker.html", form=form)

if __name__ == '__main__':
    app.run(debug=True)




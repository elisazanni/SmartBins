from flask import Flask, render_template, request

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/choose-days', methods=['GET', 'POST'])
def choose_days():
    days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    if request.method == 'POST':
        selected_days = [request.form['plastica_day'], request.form['vetro_day'], request.form['carta_day'], request.form['umido_day']]
        return render_template('index.html', selected_days=selected_days)
    return render_template('choose_days.html', days=days)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

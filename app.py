from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/time_calculator', methods=['GET', 'POST'])
def time_calculator():
    total_hours = None
    start_input = ''
    end_input = ''

    if request.method == 'POST':
        start_input = request.form.get('start_datetime')
        end_input = request.form.get('end_datetime')

        try:
            fmt = '%Y-%m-%dT%H:%M'
            start_dt = datetime.strptime(start_input, fmt)
            end_dt = datetime.strptime(end_input, fmt)

            # Handle overnight shifts
            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            tdelta = end_dt - start_dt
            total_hours = round(tdelta.total_seconds() / 3600, 2)
        except Exception as e:
            total_hours = 'Error: ' + str(e)
    else:
        # Pre-fill with current date and time
        now = datetime.now()
        start_input = now.strftime('%Y-%m-%dT%H:%M')
        end_input = now.strftime('%Y-%m-%dT%H:%M')

    return render_template('time_calculator.html', total_hours=total_hours,
                           start_input=start_input, end_input=end_input)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

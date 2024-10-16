from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/time_calculator', methods=['GET', 'POST'])
def time_calculator():
    results = {}
    if request.method == 'POST':
        # Initialize variables
        total_shift_duration = timedelta()
        start_inputs = []
        end_inputs = []
        start_formatted = []
        end_formatted = []

        # Collect shifts
        for i in range(1, 4):  # Supports up to 3 shifts
            start_input = request.form.get(f'start_datetime_{i}')
            end_input = request.form.get(f'end_datetime_{i}')
            if start_input and end_input:
                start_inputs.append(start_input)
                end_inputs.append(end_input)

                # Parse date and time inputs
                fmt = '%Y-%m-%dT%H:%M'
                start_dt = datetime.strptime(start_input, fmt)
                end_dt = datetime.strptime(end_input, fmt)

                # Handle overnight shifts
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)

                # Add to total shift duration
                shift_duration = end_dt - start_dt
                total_shift_duration += shift_duration

                # Store formatted times for display
                start_formatted.append(start_dt.strftime('%Y-%m-%d %I:%M %p'))
                end_formatted.append(end_dt.strftime('%Y-%m-%d %I:%M %p'))

        # Retrieve other inputs
        normal_shift_hours = int(request.form.get('normal_shift_hours', 8))
        normal_shift_minutes = int(request.form.get('normal_shift_minutes', 0))
        overtime_rate_input = request.form.get('overtime_rate')

        # Breaks
        paid_break_hours = int(request.form.get('paid_break_hours', 0))
        paid_break_minutes = int(request.form.get('paid_break_minutes', 0))
        unpaid_break_hours = int(request.form.get('unpaid_break_hours', 0))
        unpaid_break_minutes = int(request.form.get('unpaid_break_minutes', 0))

        # Optional Pay Information
        currency = request.form.get('currency', 'R')
        pay_frequency = request.form.get('pay_frequency', '')
        pay_rate_input = request.form.get('pay_rate', '')

        try:
            # Calculate break durations
            paid_break_duration = timedelta(hours=paid_break_hours, minutes=paid_break_minutes)
            unpaid_break_duration = timedelta(hours=unpaid_break_hours, minutes=unpaid_break_minutes)
            total_break_duration = paid_break_duration + unpaid_break_duration

            # Calculate total working time
            total_work_time = total_shift_duration - total_break_duration

            # Convert normal shift length to timedelta
            normal_shift_duration = timedelta(hours=normal_shift_hours, minutes=normal_shift_minutes)

            # Calculate regular hours and overtime hours
            if total_work_time <= normal_shift_duration:
                regular_hours = total_work_time
                overtime_hours = timedelta()
            else:
                regular_hours = normal_shift_duration
                overtime_hours = total_work_time - normal_shift_duration

            # Overtime rate
            overtime_rate = float(overtime_rate_input) if overtime_rate_input else 0.0

            # Convert times to decimal hours
            regular_hours_decimal = round(regular_hours.total_seconds() / 3600, 2)
            overtime_hours_decimal = round(overtime_hours.total_seconds() / 3600, 2)

            # Calculate adjusted overtime hours
            adjusted_overtime_hours = overtime_hours_decimal * overtime_rate

            # Calculate total equivalent hours
            total_equivalent_hours = regular_hours_decimal + adjusted_overtime_hours

            # Prepare results
            # Convert times to hours and minutes
            def format_timedelta(td):
                total_seconds = int(td.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return hours, minutes

            results.update({
                'total_shift': format_timedelta(total_shift_duration),
                'total_shift_decimal': round(total_shift_duration.total_seconds() / 3600, 2),
                'total_work_time': format_timedelta(total_work_time),
                'total_work_time_decimal': round(total_work_time.total_seconds() / 3600, 2),
                'total_break_duration': format_timedelta(total_break_duration),
                'total_break_duration_decimal': round(total_break_duration.total_seconds() / 3600, 2),
                'regular_hours': format_timedelta(regular_hours),
                'regular_hours_decimal': regular_hours_decimal,
                'overtime_hours': format_timedelta(overtime_hours),
                'overtime_hours_decimal': overtime_hours_decimal,
                'overtime_rate': overtime_rate,
                'adjusted_overtime_hours': adjusted_overtime_hours,
                'total_equivalent_hours': total_equivalent_hours,
            })

            # Calculate pay if optional data is provided
            if pay_frequency and pay_rate_input:
                try:
                    pay_rate = float(pay_rate_input)

                    # Calculate hourly rate based on pay frequency
                    if pay_frequency == 'hourly':
                        hourly_rate = pay_rate
                    elif pay_frequency == 'daily':
                        # Assuming standard 8 hours per day
                        hourly_rate = pay_rate / 8
                    elif pay_frequency == 'weekly':
                        # Assuming standard 40 hours per week
                        hourly_rate = pay_rate / 40
                    elif pay_frequency == 'monthly':
                        # Assuming standard 160 hours per month
                        hourly_rate = pay_rate / 160
                    elif pay_frequency == 'yearly':
                        # Assuming standard 1920 hours per year
                        hourly_rate = pay_rate / 1920
                    else:
                        hourly_rate = 0  # Default to zero if frequency is unknown

                    # Calculate regular pay
                    regular_pay = regular_hours_decimal * hourly_rate

                    # Calculate overtime pay
                    overtime_pay = overtime_hours_decimal * hourly_rate * overtime_rate

                    # Total pay
                    total_shift_pay = regular_pay + overtime_pay

                    # Format pay amounts
                    regular_pay_formatted = f"{currency}{regular_pay:.2f}"
                    overtime_pay_formatted = f"{currency}{overtime_pay:.2f}"
                    total_shift_pay_formatted = f"{currency}{total_shift_pay:.2f}"

                    # Store in results
                    results['regular_pay_formatted'] = regular_pay_formatted
                    results['overtime_pay_formatted'] = overtime_pay_formatted
                    results['total_shift_pay_formatted'] = total_shift_pay_formatted
                except ValueError:
                    results['error'] = 'Invalid pay rate entered.'

            # If pay information is not provided, still show total equivalent hours
            else:
                results['total_equivalent_hours'] = total_equivalent_hours

        except Exception as e:
            results['error'] = 'Error: ' + str(e)

        # Preserve form inputs
        results.update({
            'normal_shift_hours': normal_shift_hours,
            'normal_shift_minutes': normal_shift_minutes,
            'overtime_rate_input': overtime_rate_input,
            'paid_break_hours': paid_break_hours,
            'paid_break_minutes': paid_break_minutes,
            'unpaid_break_hours': unpaid_break_hours,
            'unpaid_break_minutes': unpaid_break_minutes,
            'currency': currency,
            'pay_frequency': pay_frequency,
            'pay_rate': pay_rate_input,
        })

        # Store shift inputs for reuse
        for idx in range(1, 4):
            results[f'start_input_{idx}'] = request.form.get(f'start_datetime_{idx}', '')
            results[f'end_input_{idx}'] = request.form.get(f'end_datetime_{idx}', '')

        # Store formatted times for display
        results['shifts'] = list(zip(start_formatted, end_formatted))

    else:
        # Set default values
        today = datetime.now().date()
        start_dt = datetime.combine(today, datetime.strptime('08:00', '%H:%M').time())
        end_dt = datetime.combine(today, datetime.strptime('17:00', '%H:%M').time())

        start_input = start_dt.strftime('%Y-%m-%dT%H:%M')
        end_input = end_dt.strftime('%Y-%m-%dT%H:%M')
        normal_shift_hours = 8
        normal_shift_minutes = 0
        overtime_rate_input = '1.5'

        # Initialize default shift inputs
        results.update({
            'start_input_1': start_input,
            'end_input_1': end_input,
            'start_input_2': '',
            'end_input_2': '',
            'start_input_3': '',
            'end_input_3': '',
            'normal_shift_hours': normal_shift_hours,
            'normal_shift_minutes': normal_shift_minutes,
            'overtime_rate_input': overtime_rate_input,
            'paid_break_hours': 0,
            'paid_break_minutes': 0,
            'unpaid_break_hours': 0,
            'unpaid_break_minutes': 0,
            'currency': 'R',
            'pay_frequency': '',
            'pay_rate': '',
        })

        # Store formatted times for display (empty initially)
        results['shifts'] = []

    return render_template('time_calculator.html', results=results)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

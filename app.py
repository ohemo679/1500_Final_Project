from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'any_random_string'

# Database Configuration
db_config = {
    'host': config.MYSQL_HOST,
    'user': config.MYSQL_USER,
    'password': config.MYSQL_PASSWORD,
    'database': config.MYSQL_DB
}

# Login Route

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('home'))
    return render_template('login.html')

# Home Route
# Default route redirects to login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Home route (dashboard)
@app.route('/home')
def home():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Get total applications
    cursor.execute("SELECT COUNT(*) as total FROM applicants")
    total_applications = cursor.fetchone()['total']

    # Get pending applications
    cursor.execute("SELECT COUNT(*) as pending FROM applicants WHERE status = 'pending' OR status IS NULL")
    pending_count = cursor.fetchone()['pending']

    # Calculate acceptance rate
    cursor.execute("SELECT COUNT(*) as accepted FROM applicants WHERE status = 'accepted'")
    accepted_count = cursor.fetchone()['accepted']
    acceptance_rate = round((accepted_count / total_applications * 100) if total_applications > 0 else 0, 1)

    # Get test score averages
    cursor.execute("SELECT test_name, AVG(score) as avg_score FROM test_scores GROUP BY test_name")
    test_averages = cursor.fetchall()

    conn.close()

    return render_template('home.html',
                           total_applications=total_applications,
                           pending_count=pending_count,
                           acceptance_rate=acceptance_rate,
                           test_averages=test_averages)

@app.route('/app')
def react_app():
    return render_template('react_app.html')

# Route to View Applicants
@app.route('/applicants')
def view_applicants():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM applicants")
    applicants = cursor.fetchall()
    conn.close()
    return render_template('applicants.html', applicants=applicants)

# Route to Add an Applicant
@app.route('/add_applicant', methods=['GET', 'POST'])
def add_applicant():
    if request.method == 'POST':
        name = request.form['name']
        contact_address = request.form['contact_address']
        applied_degree = request.form['applied_degree']
        year_applied = request.form['year_applied']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applicants (name, contact_address, applied_degree, year_applied)
            VALUES (%s, %s, %s, %s)
        """, (name, contact_address, applied_degree, year_applied))
        conn.commit()
        conn.close()
        return redirect(url_for('view_applicants'))
    return render_template('add_applicant.html')

# Route to View Test Scores
@app.route('/test_scores')
def view_test_scores():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ts.*, a.name as applicant_name 
        FROM test_scores ts
        JOIN applicants a ON ts.applicant_id = a.id
        ORDER BY a.name, ts.test_name
    """)
    scores = cursor.fetchall()
    conn.close()
    return render_template('test_scores.html', scores=scores)

# Route to Search Applicants
@app.route('/search_applicants', methods=['GET'])
def search_applicants():
    name = request.args.get('name', '')
    degree = request.args.get('degree', '')
    year = request.args.get('year', '')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM applicants WHERE 1=1"
    params = []

    if name:
        query += " AND name LIKE %s"
        params.append(f"%{name}%")
    if degree:
        query += " AND applied_degree = %s"
        params.append(degree)
    if year:
        query += " AND year_apply = %s"
        params.append(year)

    cursor.execute(query, params)
    applicants = cursor.fetchall()
    conn.close()
    return render_template('applicants.html', applicants=applicants)

# Route to Update Applicant Status
@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    status = request.form['status']
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("UPDATE applicants SET status = %s WHERE id = %s", (status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('view_applicants'))

# Route to Add Test Score
@app.route('/add_test_score', methods=['GET', 'POST'])
def add_test_score():
    if request.method == 'GET':
        # Handle edit mode
        score_id = request.args.get('score_id')
        if score_id:
            # Pre-fill form with existing score data
            test_name = request.args.get('test_name')
            current_score = request.args.get('current_score')
            applicant_id = request.args.get('applicant_id')

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM applicants")
            applicants = cursor.fetchall()
            conn.close()

            return render_template('add_test_score.html',
                                   applicants=applicants,
                                   edit_mode=True,
                                   score_id=score_id,
                                   selected_test=test_name,
                                   current_score=current_score,
                                   selected_applicant_id=applicant_id)

    if request.method == 'POST':
        try:
            applicant_id = int(request.form['applicant_id'])
            test_name = request.form['test_name']
            score = int(request.form['score'])

            # Validate score ranges
            score_ranges = {
                'SAT': (400, 1600),
                'ACT': (1, 36),
                'GRE': (260, 340),
            }


            if test_name in score_ranges:
                min_score, max_score = score_ranges[test_name]
                if not (min_score <= score <= max_score):
                    flash(f'Invalid score range for {test_name}. Must be between {min_score} and {max_score}.')
                    return redirect(url_for('view_test_scores'))

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Check if applicant exists
            cursor.execute("SELECT id FROM applicants WHERE id = %s", (applicant_id,))
            if not cursor.fetchone():
                flash('Invalid applicant ID')
                return redirect(url_for('view_test_scores'))

            # Check if test score already exists
            cursor.execute("""
                SELECT id FROM test_scores 
                WHERE applicant_id = %s AND test_name = %s
            """, (applicant_id, test_name))

            if cursor.fetchone():
                cursor.execute("""
                    UPDATE test_scores 
                    SET score = %s 
                    WHERE applicant_id = %s AND test_name = %s
                """, (score, applicant_id, test_name))
            else:
                cursor.execute("""
                    INSERT INTO test_scores (applicant_id, test_name, score)
                    VALUES (%s, %s, %s)
                """, (applicant_id, test_name, score))

            conn.commit()
            conn.close()
            flash('Test score added successfully')

        except ValueError:
            flash('Invalid input values')
        except Exception as e:
            flash('An error occurred while adding the test score')

        return redirect(url_for('view_test_scores'))

    # GET request - show form
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM applicants")
    applicants = cursor.fetchall()
    conn.close()

    return render_template('add_test_score.html', applicants=applicants)

# Route for score update
@app.route('/update_test_score/<int:score_id>', methods=['POST'])
def update_test_score(score_id):
    try:
        test_name = request.form['test_name']
        score = int(request.form['score'])

        # Validate score ranges
        score_ranges = {
            'SAT': (400, 1600),
            'TOEFL': (0, 120),
            'GRE': (260, 340)
        }

        if test_name in score_ranges:
            min_score, max_score = score_ranges[test_name]
            if not (min_score <= score <= max_score):
                flash(f'Invalid score range for {test_name}. Must be between {min_score} and {max_score}.')
                return redirect(url_for('view_test_scores'))

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE test_scores 
            SET test_name = %s, score = %s 
            WHERE id = %s
        """, (test_name, score, score_id))

        conn.commit()
        conn.close()
        flash('Test score updated successfully')

    except Exception as e:
        flash('An error occurred while updating the test score')

    return redirect(url_for('view_test_scores'))

# Route to View Statistics
@app.route('/statistics')
def get_statistics():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Get total applications by year
    cursor.execute("""
        SELECT year_applied, COUNT(*) as total,
        SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted
        FROM applicants
        GROUP BY year_applied
    """)
    yearly_stats = cursor.fetchall()

    # Get average scores by degree type
    cursor.execute("""
        SELECT a.applied_degree, t.test_name, AVG(t.score) as avg_score
        FROM applicants a
        JOIN test_scores t ON a.id = t.applicant_id
        GROUP BY a.applied_degree, t.test_name
    """)
    score_stats = cursor.fetchall()

    conn.close()
    return render_template('statistics.html', yearly_stats=yearly_stats, score_stats=score_stats)

# Route to get program stats
@app.route('/api/program_stats')
def get_program_stats():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            applied_degree as name,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted
        FROM applicants 
        GROUP BY applied_degree
    """)
    stats = cursor.fetchall()
    conn.close()

    return jsonify(stats)

# Route to delete applicant
@app.route('/delete_applicant/<int:id>', methods=['POST'])
def delete_applicant(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM test_scores WHERE applicant_id = %s", (id,))
    cursor.execute("DELETE FROM applicants WHERE id = %s", (id,))

    conn.commit()
    conn.close()
    flash('Applicant deleted successfully')
    return redirect(url_for('view_applicants'))

if __name__ == '__main__':
    app.run(debug=True)

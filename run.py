from flask import Flask, render_template,request,url_for,redirect,flash,session
from app.services.analytics import area_rent,get_cities,dash_kpi,get_filters,avg_income,get_listings,get_listing_detail,get_prediction,get_avg_rent,get_areas,get_city_area_map,recommend_listing
from app.services.database import get_connection,add_user,check_user,email_exists
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
import os
app.secret_key = os.environ.get("SECRET_KEY")

get_connection()
@app.route("/")
def index():
    return render_template("index.html")

@app.after_request
def add_header(response):

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
    
@app.route("/signup",methods=['GET','POST'])
def signup():
    if request.method=='POST':
        name=request.form.get('name')
        email=request.form.get('email')
        password=request.form.get('password')
        city=request.form.get('city')
        salary=request.form.get('salary')
        existing_user = email_exists(email)

        if existing_user:

            flash(
                'Account already exists with this email.',
                'error'
            )

            return render_template("signup.html")
        add_user(name,email,password,city,salary)
        flash('Signup successful. Please login to continue.', 'success')
        return redirect(url_for('login'))
    return render_template("signup.html")


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email')
        psw=request.form.get('password')
        user=check_user(email,psw)
        if user:
            session['user_id']=user[0]
            session['user_name']=user[1]
            session['user_email']=user[2]
            session['user_city']=user[4]
            session['user_salary']=user[5]
            flash('Login successful. Welcome to your dashboard.', 'success')
            return redirect(url_for("dashboard"))
        else:

            flash(
                'Invalid email or password.',
                'error'
            )
    return render_template("login.html")


@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    filters={
        'area':request.form.get('area'),
        'bhk':request.form.get('bhk'),
        'furnishing':request.form.get('furnishing'),
        'tenant_type':request.form.get('tenant_type')
    }
    selected_city=request.form.get('city') or session['user_city']
    chart_data=area_rent(selected_city) 
    cities=get_cities()
    filter_options=get_filters(selected_city)
    kpi_data=dash_kpi(selected_city,session['user_salary'],filters)
    avg_income_chart=avg_income(selected_city)
    return render_template('dashboard.html',chart_data=chart_data,cities=cities,
                           selected_city=selected_city,kpi_data=kpi_data,
                           filter_options=filter_options,filters=filters,income_chart_data=avg_income_chart)
@app.route('/listings',methods=['GET','POST'])
def listings():
    selected_city=request.values.get('city') or session['user_city']
    area_search=request.values.get('area_search', '').strip()
    cities=get_cities()
    listings=get_listings(selected_city,session['user_salary'],area_search)
    return render_template(
        'listings.html',
        cities=cities,
        listings=listings,
        selected_city=selected_city,
        area_search=area_search
    )
@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    listing=get_listing_detail(listing_id,session['user_salary'])
    return render_template('listing_detail.html',listing=listing)

@app.route('/rent-prediction',methods=['GET','POST'])
def rent_prediction():
    cities=get_cities()
    city_area_map=get_city_area_map()
    if request.method=='POST':
        area=request.form.get('area')
        session['prediction_form']=request.form.to_dict()
        predicted_rent=get_prediction(request.form)
        avg_rent=get_avg_rent(area)
        diff_percent=round(((predicted_rent-avg_rent)/avg_rent)*100,1)
        if diff_percent>10:
            market_position = "Above area average"
            difference_status='above'
        elif diff_percent < -10:
            market_position = "Below area average"
            difference_status='below'
        else:
            market_position = "Near area average"
            difference_status='near'
        
        prediction={
            'fair_rent':predicted_rent,
            'area_avg_rent':avg_rent,
            'difference_percent':diff_percent,
            'difference_status':difference_status,
            'market_position':market_position
        }
        session['metro_dist']=float(request.form.get('nearest_metro_distance_km'))
        session['commute_time']=float(request.form.get('avg_commute_time_minutes'))
        session['tenant_type']=request.form.get('tenant_type')
        session['bhk']=int(request.form.get('bhk'))
        session['furnishing']=request.form.get('furnishing')
        budget=float(request.form.get('listed_rent'))
        session['pets_allowed']=request.form.get('pets_allowed')
        affordability_ratio=(budget/session['user_salary'])*100
        if affordability_ratio < 30:
            financial_label = "Financially Healthy"

        elif affordability_ratio < 40:
            financial_label = "Moderately Affordable"

        else:
            financial_label = "Financially Risky"

        if session['metro_dist'] <= 2 and session['commute_time'] <= 30:
            personality = "Urban Explorer"
        elif affordability_ratio <= 25:
            personality = "Budget Optimizer"
        elif session['tenant_type'] == "Family" and session['bhk'] >= 2:
            personality = "Family Comfort"
        elif session['user_salary'] > 100000 and session['furnishing'] == "Furnished":
            personality = "Luxury Seeker"
        else:
            personality = "Not decisive"
        badges=[]
        if session['metro_dist'] <= 2:
            badges.append('Near Metro')
        if session['commute_time'] <= 30:
            badges.append('Low Commute')
        if session['furnishing'] == "Furnished":
            badges.append('Furnished')
        if session['pets_allowed'] == "Yes":
            badges.append('Pet Friendly')
        if session['tenant_type'] == "Bachelor":   
            badges.append('Bachelor Friendly')
            print(session['metro_dist'])
        salary = float(session['user_salary'])

        # AFFORDABILITY SCORE

        affordability_ratio = (budget / salary) * 100

        if affordability_ratio <= 25:
            affordability_score = 100

        elif affordability_ratio <= 30:
            affordability_score = 85

        elif affordability_ratio <= 40:
            affordability_score = 65

        else:
            affordability_score = 40


        # COMMUTE SCORE

        commute_score = 100

        commute_score -= session['commute_time'] * 1.5

        commute_score -= session['metro_dist'] * 8

        commute_score = max(0, min(100, commute_score))


        # AMENITIES SCORE

        amenities_score = 0

        if session['furnishing'] == "Furnished":
            amenities_score += 35

        if request.form.get('parking_available') == "Yes":
            amenities_score += 35

        if session['pets_allowed'] == "Yes":
            amenities_score += 30


        # FINAL MATCH SCORE

        match_score = (
            affordability_score * 0.40 +
            commute_score * 0.30 +
            amenities_score * 0.30
        )

        match_score = round(match_score)

        session['match_score'] = match_score  
        difference=avg_rent-predicted_rent 
        recommend_listings=recommend_listing(request.form)
        return render_template('rent_prediction.html',cities=cities,
                               prediction=prediction,form_data=request.form,city_area_map=city_area_map,recommended_listings=recommend_listings,
                               financial_label=financial_label,personality=personality,badges=badges,match_score=match_score)
    return render_template('rent_prediction.html',cities=cities,form_data={},city_area_map=city_area_map,recommended_listings={},financial_label='cant figure now',personality='undefined',badges=[],match_score=0)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
if __name__ == "__main__":
    app.run(debug=True)

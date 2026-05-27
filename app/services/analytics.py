from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import pandas as pd


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "rental_data_enhanced.csv"


def load_rental_data():
    df = pd.read_csv(DATA_FILE)
    return df.dropna()


def area_rent(city):
    df = load_rental_data()
    city_df=df[df['city']==city]
    avg_rent = (
        city_df.groupby("area", as_index=False)["rent"]
        .mean()
        .sort_values("area")
    )

    return {
        "city":city,
        "areas": avg_rent["area"].tolist(),
        "avg_rents": avg_rent["rent"].round(0).astype(int).tolist(),
    }
def get_cities():
    df=load_rental_data()
    return df['city'].unique().tolist()

def get_filters(city):
    df=load_rental_data()
    df_city=df[df['city']==city]
    areas=sorted(df_city['area'].unique().tolist())
    bhk=sorted(df_city['bhk'].unique().tolist())
    furnishing=sorted(df_city['furnishing'].unique().tolist())
    tenant_type=sorted(df_city['tenant_type'].unique().tolist())
    return{'areas':areas,'bhks':bhk,'furnishings':furnishing,'tenant_types':tenant_type}

def dash_kpi(city,salary,filters=None):
    df=load_rental_data()
    city_df=df[df['city']==city]
    if filters:
        if filters.get("area"):
            city_df = city_df[city_df["area"] == filters["area"]]

        if filters.get("bhk"):
            city_df = city_df[city_df["bhk"] == int(filters["bhk"])]

        if filters.get("furnishing"):
            city_df = city_df[city_df["furnishing"] == filters["furnishing"]]

        if filters.get("tenant_type"):
            city_df = city_df[city_df["tenant_type"] == filters["tenant_type"]]
    listing_count=city_df.nunique().sum()
    avg_rent=city_df['rent'].mean()
    avg_size=city_df['size_sqft'].mean()
    affordable_rent=salary*0.3
    idx=(affordable_rent/avg_rent)*100
    if city_df.empty:
        return {
            "lc": 0,
            "avg_rent": 0,
            "avg_size": 0,
            "affordability_index": 0
        }
    return {
        'lc':listing_count,'avg_rent':avg_rent,'avg_size':avg_size,'affordability_index':min(100,round(idx,1))
    }

def avg_income(city):
    df=load_rental_data()
    city_df=df[df['city']==city]
    avg_income=city_df.groupby('area')['avg_income'].mean()
    return {'areas':city_df['area'].unique().tolist(),'avg_income':avg_income.round(0).astype(int).tolist()}

def get_listings(city,salary,area_search=None):
    df=load_rental_data()
    city_df=df[df['city']==city].copy()
    city_df['id']=city_df.index
    if area_search:
        city_df=city_df[city_df['area'].str.contains(area_search, case=False, na=False)]
    city_df['affordability_percent']=((salary*0.3)/city_df['rent']*100).round(1)
    city_df['affordability_percent']=city_df['affordability_percent'].clip(upper=100)
    return city_df.to_dict(orient='records')

def get_listing_detail(listing_id,salary):
    df=load_rental_data()
    row=df.loc[int(listing_id)].copy()
    city_df=df[df['city']==row['city']]
    row['id']=int(listing_id)
    row['neighborhood_score']=cal_neighborhood_score(row['city'],city_df,listing_id)
    row['property_score']=cal_property_score(row,city_df,listing_id)
    row['affordability_percent']=min(100, round(((salary * 0.3) / row["rent"]) * 100, 1))
    predicted_rent=get_price_status(listing_id)
    difference=((row['rent']-predicted_rent)/predicted_rent)*100
    if difference>15:
        row['price_status']='overpriced'
    elif (difference>-15) and  (difference<15):
        row['price_status']='Fair Priced'
    else:
        row['price_status']='Great Deal'
    return row.to_dict()

def cal_neighborhood_score(city,city_df,listing_id):
    row=city_df.loc[int(listing_id)].copy()
    row['id']=int(listing_id)
    min_metro_city=city_df['nearest_metro_distance_km'].min()
    max_metro_city=city_df['nearest_metro_distance_km'].max()
    min_mall_city=city_df['nearest_mall_distance_km'].min()
    max_mall_city=city_df['nearest_mall_distance_km'].max()
    min_hospital_city=city_df['nearest_hospital_distance_km'].min()
    max_hospital_city=city_df['nearest_hospital_distance_km'].max()
    min_school_city=city_df['nearest_school_distance_km'].min()
    max_school_city=city_df['nearest_school_distance_km'].max()
    min_park_city=city_df['nearest_park_distance_km'].min()
    max_park_city=city_df['nearest_park_distance_km'].max()
    min_commute_city=city_df['avg_commute_time_minutes'].min()
    max_commute_city=city_df['avg_commute_time_minutes'].max()
    metro_Score=100*(1-(row['nearest_metro_distance_km']-min_metro_city)/(max_metro_city-min_metro_city))
    metro_Score=max(0,min(100,metro_Score))
    mall_Score=100*(1-(row['nearest_mall_distance_km']-min_mall_city)/(max_mall_city-min_mall_city))
    mall_Score=max(0,min(100,mall_Score))
    hospital_Score=100*(1-(row['nearest_hospital_distance_km']-min_hospital_city)/(max_hospital_city-min_hospital_city))
    hospital_Score=max(0,min(100,hospital_Score))
    school_Score=100*(1-(row['nearest_school_distance_km']-min_school_city)/(max_school_city-min_school_city))
    school_Score=max(0,min(100,school_Score))
    park_Score=100*(1-(row['nearest_park_distance_km']-min_park_city)/(max_park_city-min_park_city))
    park_Score=max(0,min(100,park_Score))
    commute_Score=100*(1-(row['avg_commute_time_minutes']-min_commute_city)/(max_commute_city-min_commute_city))
    commute_Score=max(0,min(100,commute_Score))
    final_score=(
        0.25*metro_Score+
        0.15*hospital_Score+
        0.15*school_Score+
        0.10*mall_Score+
        0.10*park_Score+
        0.25*commute_Score
    )
    row['neighborhood_score']=max(0,min(100,final_score))
    return row['neighborhood_score']

def cal_property_score(row, city_df,listing_id):
    row=city_df.loc[int(listing_id)].copy()
    row['id']=int(listing_id)
    max_rent=city_df['rent'].max()
    min_rent=city_df['rent'].min()
    max_size=city_df['size_sqft'].max()
    min_size=city_df['size_sqft'].min()
    max_deposit=city_df['deposit_amount'].max()
    min_deposit=city_df['deposit_amount'].min()
    max_deposit=city_df['deposit_amount'].max()
    max_maintainance=city_df['maintenance_charges'].max()
    min_maintainance=city_df['maintenance_charges'].min()
    rent_score=100*(1-(row['rent']-min_rent)/(max_rent-min_rent))
    rent_score =max(0,min(100,rent_score))
    size_score =100*(1-(row['size_sqft']-min_rent)/(max_size-min_size))
    size_score = max(0,min(100,size_score))
    deposit_score =100*(1-(row['deposit_amount']-min_deposit)/(max_deposit-min_deposit))
    maintenance_score =100*(1-(row['maintenance_charges']-min_maintainance)/(max_maintainance-min_maintainance))
    parking_score = 100 if row["parking_available"] == "Yes" else 50
    pets_score = 100 if row["pets_allowed"] == "Yes" else 70

    final_score = (
        0.30 * rent_score +
        0.25 * size_score +
        0.15 * deposit_score +
        0.15 * maintenance_score +
        0.10 * parking_score +
        0.05 * pets_score
    )

    return max(0, min(100, round(final_score, 1)))
def learn_model():
    df=load_rental_data()
    model=RandomForestRegressor(n_estimators=100,random_state=42)
    x_df=df.drop('rent',axis=1)
    x=pd.get_dummies(x_df)
    y=df['rent']
    x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.2,random_state=42)
    model.fit(x_train,y_train)
    y_pred=model.predict(x_test)
    return model,x.columns
def get_prediction(form_data):
    model,columns=learn_model()
    input_data={
        "city": form_data.get("city"),
        "area": form_data.get("area"),
        "bhk": int(form_data.get("bhk")),
        "size_sqft": float(form_data.get("size_sqft")),
        "furnishing": form_data.get("furnishing"),
        "tenant_type": form_data.get("tenant_type"),
        "deposit_amount": float(form_data.get("deposit_amount") or 0),
        "maintenance_charges": float(form_data.get("maintenance_charges") or 0),
        "floor_number": float(form_data.get("floor_number") or 0),
        "parking_available": form_data.get("parking_available"),
        "pets_allowed": form_data.get("pets_allowed"),
        "nearest_metro_distance_km": float(form_data.get("nearest_metro_distance_km") or 0),
        "nearest_mall_distance_km": float(form_data.get("nearest_mall_distance_km") or 0),
        "nearest_hospital_distance_km": float(form_data.get("nearest_hospital_distance_km") or 0),
        "nearest_school_distance_km": float(form_data.get("nearest_school_distance_km") or 0),
        "nearest_park_distance_km": float(form_data.get("nearest_park_distance_km") or 0),
        "avg_commute_time_minutes": float(form_data.get("avg_commute_time_minutes") or 0),
    }
    input_df=pd.DataFrame([input_data])
    input_df=pd.get_dummies(input_df)
    input_df=input_df.reindex(columns=columns,fill_value=0)
    predicted_rent=model.predict(input_df)[0]
    return round(predicted_rent,0)

def get_avg_rent(area):
    df=load_rental_data()
    area_df=df[df['area']==area].copy()
    avg_rent=area_df['rent'].mean()
    return avg_rent

def get_areas(city):
    df=load_rental_data()
    city_df=df[df['city']==city].copy()
    return city_df['area'].unique().tolist()

def get_city_area_map():
    df = load_rental_data()
    city_area_map = {}

    for city in df["city"].dropna().unique():
        city_df = df[df["city"] == city]
        city_area_map[city] = sorted(city_df["area"].dropna().unique().tolist())

    return city_area_map

def get_price_status(listing_id):
    df=load_rental_data()
    row=df.loc[int(listing_id)].copy()
    model, columns=learn_model()
    listing_data={
        'city':row['city'],
        'area':row['area'],
        'bhk':row['bhk'],
        'size_sqft':row['size_sqft'],
        'furnishing':row['furnishing'],
        'tenant_type':row['tenant_type'],
        'deposit_amount':row['deposit_amount'],
        'maintenance_charges':row['maintenance_charges'],
        'floor_number':row['floor_number'],
        'parking_available':row['parking_available'],
        'pets_allowed':row['pets_allowed'],
        'nearest_metro_distance_km':row['nearest_metro_distance_km'],
        'nearest_mall_distance_km':row['nearest_mall_distance_km'],
        'nearest_hospital_distance_km':row['nearest_hospital_distance_km'],
        'nearest_school_distance_km':row['nearest_school_distance_km'],
        'nearest_park_distance_km':row['nearest_park_distance_km'],
        'avg_commute_time_minutes':row['avg_commute_time_minutes']
     }
    x_test=pd.DataFrame([listing_data])
    x_test=pd.get_dummies(x_test)
    x_test=x_test.reindex(columns=columns,fill_value=0)
    predicted_rent=model.predict(x_test)[0]
    return round(predicted_rent,0 )

def recommend_listing(form_data):
    df=load_rental_data()
    matching_df = df[
        (df["city"] == form_data.get("city")) &
        (df["area"] == form_data.get("area")) &
        (df["bhk"] == int(form_data.get("bhk"))) &
        (df["furnishing"] == form_data.get("furnishing")) &
        (df["tenant_type"] == form_data.get("tenant_type"))
    ]
    matching_df["budget_gap"] = float(form_data.get('listed_rent')) - matching_df["rent"]
    matching_df = matching_df[matching_df["budget_gap"] >= 0]
    matching_df = matching_df.sort_values(["rent", "size_sqft"], ascending=[True, False])
    matching_df['id']=matching_df.index
    return matching_df.to_dict(orient='records')


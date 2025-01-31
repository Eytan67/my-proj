import pandas as pd
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app.database.load_data import session_maker
from app.models.event import Event



def find_deadliest_attack_style():
    with session_maker() as session:
        try:
            results = session.query(
                Event.attack_type,
                func.sum(func.coalesce(Event.n_kill, 0)).label('total_kills'),
                func.sum(func.coalesce(Event.n_wound, 0)).label('total_wounds')
            ).group_by(Event.attack_type).all()

            df = pd.DataFrame(results, columns=['Attack_Type', 'Total_Kills', 'Total_Wounds'])
            df['score'] = (df['Total_Kills'] * 2) + df['Total_Wounds']
            sorted_df = df.sort_values(by='score', ascending=False)
            return sorted_df
        except Exception as e:
            print(f"An error occurred: {e}")

def find_average_casualties_by_region():
    with session_maker() as session:
        try:
            results = session.query(
                Event.region,
                (func.sum(func.coalesce(Event.n_kill, 0)) * 2 + func.sum(func.coalesce(Event.n_wound, 0))).label('score'),
                func.count()
            ).group_by(Event.region).all()
            df = pd.DataFrame(results, columns=['region', 'score', 'count'])
            df['score_per_count'] = df['score'] / df['count']

            return df[['region', 'score_per_count']]
        except Exception as e:
            print(f"An error occurred: {e}")

def find_most_aggressive_groups():
    with session_maker() as session:
        try:
            results = session.query(
                Event.g_name,
                func.sum(func.coalesce(Event.n_kill, 0)).label('total_kills'),
                func.sum(func.coalesce(Event.n_wound, 0)).label('total_wounds')
            ).group_by(Event.g_name).all()

            df = pd.DataFrame(results, columns=['g_name', 'total_kills', 'total_wounds'])
            df['score'] = df['total_kills'] + df['total_wounds']
            sorted_df = df.sort_values(by='score', ascending=False)
            return sorted_df
        except Exception as e:
            print(f"An error occurred: {e}")

def find_change_percent_by_region():
    with session_maker() as session:
        try:
            results = session.query(
                Event.region,
                Event.year,
                func.count(Event.id).label('count')
            ).group_by(Event.region, Event.year).all()
            df = pd.DataFrame(results, columns=['region', 'year', 'count'])
            df = df.sort_values(by=['region', 'year'])
            df['change'] = df.groupby('region')['count'].pct_change() * 100
            avg_change = df.groupby('region')['change'].mean().reset_index()
            return avg_change
        except Exception as e:
            print(f"An error occurred: {e}")

def find_top_5_by_region(region=None):
    with session_maker() as session:
        try:
            results = session.query(
                Event.region,
                Event.g_name,
                func.count(Event.id).label('count')
            ).group_by(Event.region, Event.g_name).order_by(Event.region, func.count(Event.id).desc()).all()
            df = pd.DataFrame(results, columns=['region', 'group name', 'count'])
            result = df.groupby('region').apply(lambda x: x.nlargest(5, 'count'))
            if region:
                result = result[result['region'] == region]
            return result
        except Exception as e:
            print(f"An error occurred: {e}")
analysis_bp = Blueprint('analysis', __name__)

# 1.
@analysis_bp.route('/deadliest', methods=['GET'])
def deadliest_attack_style():
    res = find_deadliest_attack_style()
    limit = request.args.get('limit', default=None)
    if limit:
        res = res.head(5)
    res_json = res.to_dict('records')

    return jsonify(res_json)

# 2.
@analysis_bp.route('/victims_by_region', methods=['GET'])
def average_casualties_by_region():
    res = find_average_casualties_by_region()
    limit = request.args.get('limit', default=None)
    if limit:
        res = res.head(5)
    res_json = res.to_dict('records')

    return jsonify(res_json)

# 3.
@analysis_bp.route('/most_aggressive', methods=['GET'])
def most_aggressive_groups():
    res = find_most_aggressive_groups().head(5).to_dict('records')

    return jsonify(res)

# 6.
@analysis_bp.route('/change_percent_by_region', methods=['GET'])
def change_percent_by_region():
    res = find_change_percent_by_region()
    limit = request.args.get('limit', default=None)
    if limit:
        res = res.head(5)
    res_json = res.to_dict('records')

    return jsonify(res_json)

# 8.
@analysis_bp.route('/top_5_by_country_region', methods=['GET'])
def top_5_by_region():
    region = request.args.get('region', default=None)
    res = find_top_5_by_region(region)

    res_json = res.to_dict('records')

    return jsonify(res_json)
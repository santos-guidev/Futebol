import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from textblob import TextBlob
import requests

# Constants
TEST_SIZE = 0.3
RANDOM_STATE = 42

# Load data from URL
@st.cache_data
def load_data(url):
    """Carrega e retorna dados de um arquivo Excel da URL fornecida."""
    try:
        return pd.read_excel(url)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Lista de URLs dos bancos de dados disponíveis
DATA_SOURCES = {
    'Argentina Primeira Division': 'https://github.com/futpythontrader/YouTube/raw/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2024)/Argentina%20Primera%20Divisi%C3%B3n_2024.xlsx',
    'Brasileirão Serie A': 'https://github.com/futpythontrader/YouTube/raw/main/Bases_de_Dados/FootyStats/Bases_de_Dados_(2022-2024)/Brazil%20Serie%20A_2024.xlsx'
}

def get_recent_stats(team, data):
    """Obtém estatísticas dos últimos 5 jogos de uma equipe."""
    recent_matches = data[(data['Home'] == team) | (data['Away'] == team)].tail(5)
    recent_matches['Date'] = pd.to_datetime(recent_matches['Date']).dt.strftime('%d-%m-%Y %H:%M')
    
    recent_stats = recent_matches[['Date', 'Home', 'Away', 'Goals_H_FT', 'Goals_A_FT', 'ShotsOnTarget_H', 'ShotsOnTarget_A', 'ShotsOffTarget_H', 'ShotsOffTarget_A', 'Corners_H_FT', 'Corners_A_FT']]
    return recent_stats

def get_home_away_stats(team, data):
    """Obtém estatísticas de desempenho em casa e fora."""
    home_stats = data[data['Home'] == team].agg({
        'Goals_H_FT': ['mean', 'sum'],
        'Goals_A_FT': ['mean', 'sum'],
        'ShotsOnTarget_H': 'mean',
        'ShotsOffTarget_H': 'mean',
        'Corners_H_FT': 'mean'
    }).to_dict()
    
    away_stats = data[data['Away'] == team].agg({
        'Goals_A_FT': ['mean', 'sum'],
        'Goals_H_FT': ['mean', 'sum'],
        'ShotsOnTarget_A': 'mean',
        'ShotsOffTarget_A': 'mean',
        'Corners_A_FT': 'mean'
    }).to_dict()
    
    stats = {
        'home': {
            'Avg Goals Scored': home_stats['Goals_H_FT']['mean'],
            'Total Goals Scored': home_stats['Goals_H_FT']['sum'],
            'Avg Goals Conceded': home_stats['Goals_A_FT']['mean'],
            'Total Goals Conceded': home_stats['Goals_A_FT']['sum'],
            'Avg Shots on Target': home_stats['ShotsOnTarget_H'],
            'Avg Shots off Target': home_stats['ShotsOffTarget_H'],
            'Avg Corners': home_stats['Corners_H_FT']
        },
        'away': {
            'Avg Goals Scored': away_stats['Goals_A_FT']['mean'],
            'Total Goals Scored': away_stats['Goals_A_FT']['sum'],
            'Avg Goals Conceded': away_stats['Goals_H_FT']['mean'],
            'Total Goals Conceded': away_stats['Goals_H_FT']['sum'],
            'Avg Shots on Target': away_stats['ShotsOnTarget_A'],
            'Avg Shots off Target': away_stats['ShotsOffTarget_A'],
            'Avg Corners': away_stats['Corners_A_FT']
        }
    }
    return stats

def calculate_average_odds(data):
    """Calcula as odds médias para o time da casa e o time visitante."""
    avg_odds = {
        'Home Win': data['Odd_H_FT'].mean(),
        'Draw': data['Odd_D_FT'].mean(),
        'Away Win': data['Odd_A_FT'].mean()
    }
    
    odds_over_under = {
        'Over 0.5': data[['Odd_Over05_FT', 'Odd_Over05_HT']].mean().mean(),
        'Under 0.5': data[['Odd_Under05_FT', 'Odd_Under05_HT']].mean().mean(),
        'Over 1.5': data[['Odd_Over15_FT', 'Odd_Over15_HT']].mean().mean(),
        'Under 1.5': data[['Odd_Under15_FT', 'Odd_Under15_HT']].mean().mean(),
        'Over 2.5': data[['Odd_Over25_FT', 'Odd_Over25_HT']].mean().mean(),
        'Under 2.5': data[['Odd_Under25_FT', 'Odd_Under25_HT']].mean().mean()
    }
    
    return avg_odds, odds_over_under

def check_columns(data):
    """Verifica se as colunas necessárias estão presentes no DataFrame."""
    required_columns = [
        'ShotsOnTarget_H', 'ShotsOnTarget_A', 
        'ShotsOffTarget_H', 'ShotsOffTarget_A', 
        'Corners_H_FT', 'Corners_A_FT', 
        'Odd_H_FT', 'Odd_D_FT', 'Odd_A_FT',
        'Odd_Over05_FT', 'Odd_Over05_HT', 
        'Odd_Under05_FT', 'Odd_Under05_HT',
        'Odd_Over15_FT', 'Odd_Over15_HT',
        'Odd_Under15_FT', 'Odd_Under15_HT',
        'Odd_Over25_FT', 'Odd_Over25_HT',
        'Odd_Under25_FT', 'Odd_Under25_HT'
    ]
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Faltam colunas no DataFrame: {', '.join(missing_columns)}")
        return False
    return True

def plot_stats(home_team, away_team, home_away_stats, away_away_stats, avg_odds, odds_over_under, data):
    """Plota gráficos das estatísticas."""
    # Estatísticas Casa
    home_away_df = pd.DataFrame(home_away_stats['home'], index=[home_team])
    fig_home = px.bar(home_away_df.T, title=f'Estatísticas de {home_team} como Mandante', labels={'index': 'Stat', 'value': 'Quantity'})
    
    # Estatísticas Fora
    away_away_df = pd.DataFrame(away_away_stats['away'], index=[away_team])
    fig_away = px.bar(away_away_df.T, title=f'Estatísticas de {away_team} como Visitante', labels={'index': 'Stat', 'value': 'Quantity'})
    
    # Odds Médias
    odds_df = pd.DataFrame(list(avg_odds.items()), columns=['Outcome', 'Average Odds'])
    fig_odds = px.bar(odds_df, x='Outcome', y='Average Odds', title='Odds Médias')
    
    # Odds Over/Under
    odds_over_under_df = pd.DataFrame(list(odds_over_under.items()), columns=['Type', 'Average Odds'])
    fig_odds_over_under = px.bar(odds_over_under_df, x='Type', y='Average Odds', title='Odds Over/Under')

    # Chutes e Cantos
    if all(col in data.columns for col in ['ShotsOnTarget_H', 'ShotsOnTarget_A', 'ShotsOffTarget_H', 'ShotsOffTarget_A', 'Corners_H_FT', 'Corners_A_FT']):
        shots_on_target = data[['ShotsOnTarget_H', 'ShotsOnTarget_A']].mean().reset_index()
        shots_on_target.columns = ['Type', 'Average Shots on Target']
        fig_shots_on_target = px.bar(shots_on_target, x='Type', y='Average Shots on Target', title='Chutes no Alvo')
        
        shots_off_target = data[['ShotsOffTarget_H', 'ShotsOffTarget_A']].mean().reset_index()
        shots_off_target.columns = ['Type', 'Average Shots off Target']
        fig_shots_off_target = px.bar(shots_off_target, x='Type', y='Average Shots off Target', title='Chutes Fora do Alvo')
        
        corners = data[['Corners_H_FT', 'Corners_A_FT']].mean().reset_index()
        corners.columns = ['Type', 'Average Corners']
        fig_corners = px.bar(corners, x='Type', y='Average Corners', title='Cantos')

    # Exibição dos Gráficos
    st.plotly_chart(fig_home)
    st.plotly_chart(fig_away)
    st.plotly_chart(fig_odds)
    st.plotly_chart(fig_odds_over_under)
    
    if 'fig_shots_on_target' in locals():
        st.plotly_chart(fig_shots_on_target)
        st.plotly_chart(fig_shots_off_target)
        st.plotly_chart(fig_corners)

def analyze_sentiment(text):
    """Analisa o sentimento do texto usando TextBlob."""
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "Positivo"
    elif analysis.sentiment.polarity == 0:
        return "Neutro"
    else:
        return "Negativo"

def main():
    st.title("Análise de Dados de Futebol")
    
    # Seleção de banco de dados
    selected_data_source = st.selectbox("Selecione o banco de dados", list(DATA_SOURCES.keys()))
    data_url = DATA_SOURCES[selected_data_source]
    data = load_data(data_url)
    
    if data is not None and check_columns(data):
        # Seleção de times
        team1 = st.selectbox("Selecione o time da Casa", data['Home'].unique())
        team2 = st.selectbox("Selecione o time Visitante", data['Away'].unique())
        
        if team1 and team2:
            home_away_stats = get_home_away_stats(team1, data)
            away_away_stats = get_home_away_stats(team2, data)
            avg_odds, odds_over_under = calculate_average_odds(data)
            
            # Exibição das Estatísticas
            st.subheader(f"Estatísticas Recentes dos Últimos 5 Jogos de {team1}")
            recent_stats_team1 = get_recent_stats(team1, data)
            st.write(recent_stats_team1)
            
            st.subheader(f"Estatísticas Recentes dos Últimos 5 Jogos de {team2}")
            recent_stats_team2 = get_recent_stats(team2, data)
            st.write(recent_stats_team2)
            
            plot_stats(team1, team2, home_away_stats, away_away_stats, avg_odds, odds_over_under, data)

if __name__ == "__main__":
    main()

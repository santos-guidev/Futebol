import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Constants
TEST_SIZE = 0.3
RANDOM_STATE = 42

# Load data from URL
@st.cache
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
    fig, ax = plt.subplots(3, 2, figsize=(20, 18))
    
    # Estatísticas Casa
    home_away_df = pd.DataFrame(home_away_stats['home'], index=[home_team])
    home_away_df.T.plot(kind='bar', ax=ax[0, 0], color=['blue', 'red'])
    ax[0, 0].set_title(f'Estatísticas de {home_team} como Mandante')
    ax[0, 0].set_ylabel('Quantidade')
    ax[0, 0].tick_params(axis='x', rotation=45)

    # Estatísticas Fora
    away_away_df = pd.DataFrame(away_away_stats['away'], index=[away_team])
    away_away_df.T.plot(kind='bar', ax=ax[0, 1], color=['blue', 'red'])
    ax[0, 1].set_title(f'Estatísticas de {away_team} como Visitante')
    ax[0, 1].set_ylabel('Quantidade')
    ax[0, 1].tick_params(axis='x', rotation=45)

    # Odds Médias
    odds_df = pd.DataFrame(list(avg_odds.items()), columns=['Outcome', 'Average Odds'])
    sns.barplot(x='Outcome', y='Average Odds', data=odds_df, ax=ax[1, 0], palette='viridis')
    ax[1, 0].set_title('Odds Médias')
    ax[1, 0].set_ylabel('Odds')
    
    # Odds Over/Under
    odds_over_under_df = pd.DataFrame(list(odds_over_under.items()), columns=['Type', 'Average Odds'])
    sns.barplot(x='Type', y='Average Odds', data=odds_over_under_df, ax=ax[1, 1], palette='viridis')
    ax[1, 1].set_title('Odds Over/Under')
    ax[1, 1].set_ylabel('Odds')

    # Chutes e Cantos
    if all(col in data.columns for col in ['ShotsOnTarget_H', 'ShotsOnTarget_A', 'ShotsOffTarget_H', 'ShotsOffTarget_A', 'Corners_H_FT', 'Corners_A_FT']):
        fig_shots_corners, ax_shots_corners = plt.subplots(2, 2, figsize=(15, 10))
        
        # Chutes no Alvo
        data[['ShotsOnTarget_H', 'ShotsOnTarget_A']].mean().plot(kind='bar', ax=ax_shots_corners[0, 0])
        ax_shots_corners[0, 0].set_title('Chutes no Alvo')
        
        # Chutes Fora do Alvo
        data[['ShotsOffTarget_H', 'ShotsOffTarget_A']].mean().plot(kind='bar', ax=ax_shots_corners[0, 1])
        ax_shots_corners[0, 1].set_title('Chutes Fora do Alvo')
        
        # Cantos
        data[['Corners_H_FT', 'Corners_A_FT']].mean().plot(kind='bar', ax=ax_shots_corners[1, 0])
        ax_shots_corners[1, 0].set_title('Cantos')
    
    st.pyplot(fig)
    if 'fig_shots_corners' in locals():
        st.pyplot(fig_shots_corners)

def main():
    st.sidebar.title("Análise de Dados Esportivos")
    
    # Seleção da Fonte de Dados
    source = st.sidebar.selectbox("Escolha o Banco de Dados", options=DATA_SOURCES.keys())
    data_url = DATA_SOURCES[source]
    data = load_data(data_url)
    
    if data is not None and check_columns(data):
        # Seleção dos Times
        home_team = st.sidebar.selectbox("Escolha o Time da Casa", options=data['Home'].unique())
        away_team = st.sidebar.selectbox("Escolha o Time Visitante", options=data['Away'].unique())
        
        st.title(f"Análise de {home_team} vs {away_team}")
        
        # Estatísticas dos Últimos Jogos
        recent_stats_home = get_recent_stats(home_team, data)
        recent_stats_away = get_recent_stats(away_team, data)
        
        st.subheader(f"Estatísticas dos Últimos 5 Jogos de {home_team}")
        st.write(recent_stats_home)
        
        st.subheader(f"Estatísticas dos Últimos 5 Jogos de {away_team}")
        st.write(recent_stats_away)
        
        # Estatísticas de Desempenho
        home_away_stats = get_home_away_stats(home_team, data)
        away_away_stats = get_home_away_stats(away_team, data)
        
        # Odds
        avg_odds, odds_over_under = calculate_average_odds(data)
        
        # Plotagem
        plot_stats(home_team, away_team, home_away_stats, away_away_stats, avg_odds, odds_over_under, data)

if __name__ == "__main__":
    main()

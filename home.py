import json
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as subplots
import streamlit as st
import zipfile


def get_racer_name(car_id:str) -> str:
    return cars_dict[car_id]["alias"]

def get_racer_names(car_ids:pd.Series) -> pd.Series:
    return car_ids.apply(get_racer_name)

def get_racer_team(car_id:str) -> str:
    decal_path:str = cars_dict[car_id]["front_decal_path"]
    if decal_path.endswith("question-mark.png"):
        return "Bem Aleatório"
    elif decal_path.endswith("bread-search.png"):
        return "BFS"
    elif decal_path.endswith("quimera.png"):
        return "Quimera"
    elif decal_path.endswith("wolf-69.png"):
        return "Machos Alfanuméricos"
    elif decal_path.endswith("marcha-atras.png"):
        return "Marcha-atrás"
    elif decal_path.endswith("meta-morfada.png"):
        return "Meta-morfada"
    elif decal_path.endswith("astrogoblin.png"):
        return "Viúvas do Funhaus"
    else:
        return ""

def get_racer_teams(car_ids:pd.Series) -> pd.Series:
    return car_ids.apply(get_racer_team)

def get_standings_df(race_id:str, format_text:bool=False) -> pd.DataFrame:
    standings_dict:dict = races_dict[race_id]["standings"]
    _df:pd.DataFrame = pd.DataFrame.from_records(list(standings_dict.values()))
    _df = _df.rename(columns={"car_id":"Corredor", "finished":"Concluiu", "elapsed_time":"Tempo", "max_progress":"Distância"})
    _df["Tempo"] = _df["Tempo"].where(_df["Concluiu"], None)
    _df = _df.drop(columns=["Concluiu"])
    _df = _df.sort_values(["Tempo", "Distância"], ascending=[True, False])
    _df = _df.reset_index(drop=True)
    _df["Posição"] = _df.index+1
    _df = _df.set_index(_df["Corredor"])
    _df.index.name = None
    _df["Equipe"] = get_racer_teams(_df["Corredor"])
    _df["Corredor"] = get_racer_names(_df["Corredor"])
    _df = _df.reindex(columns=["Posição", "Corredor", "Tempo", "Distância", "Equipe"])
    if format_text:
        _df["Distância"] = _df["Distância"].apply(lambda x: f"{x:.1f}m")
        _df["Tempo"] = _df["Tempo"].apply(lambda x: f"{x:.1f}s")
        _df["Tempo"] = _df["Tempo"].where(_df["Tempo"].isna(), "DNF")
    return _df

def get_min_time(df:pd.DataFrame) -> pd.Series:
    return df.loc[df["finished"]]["elapsed_time"].min()

def get_4th_time(df:pd.DataFrame) -> pd.Series:
    return df.loc[df["finished"]]["elapsed_time"].min()

def get_Nth_best(series:pd.Series, n:int=0, asc:bool=True) -> float:
    return series.sort_values(ascending=asc, ignore_index=True)[n]

def get_evolution_df(exp_id:str) -> pd.DataFrame:
    race_ids:list[str] = experiments_dict[exp_id]["races"]

    dfs:list[pd.DataFrame] = []
    for race_id in race_ids:
        _df:pd.DataFrame = get_standings_df(race_id)
        _df["Corrida"] = race_id
        dfs.append(_df)
    df:pd.DataFrame = pd.concat(dfs)
    
    evolution_df:pd.DataFrame = df.groupby("Corrida").agg(
        top1_progress=pd.NamedAgg(
            "Distância", lambda x: get_Nth_best(x, asc=False)),
        top4_progress=pd.NamedAgg(
            "Distância", lambda x: get_Nth_best(x, n=3, asc=False)),
        top1_time=pd.NamedAgg(
            "Tempo", lambda x: get_Nth_best(x)),
        top4_time=pd.NamedAgg(
            "Tempo", lambda x: get_Nth_best(x, n=3)))
    evolution_df = evolution_df.reset_index()
    return evolution_df

def get_evolution_plot(exp_id:str) -> go.Figure:
    evolution_df:pd.DataFrame = get_evolution_df(exp_id)
    fig = subplots.make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=.2,
        subplot_titles=["Distância percorrida", "Tempo para completar"])
    fig.add_trace({
            "type":"scatter", "mode":"lines",
            "name":"Top1",
            "legendgroup":"top1",
            "x":evolution_df.index+1, "y":evolution_df["top1_progress"],
            "line":{"color":"#002552"}},
        row=1, col=1)
    fig.add_trace({
            "type":"scatter", "mode":"lines",
            "name":"Top4",
            "legendgroup":"top4",
            "x":evolution_df.index+1, "y":evolution_df["top4_progress"],
            "line":{"dash":"dot", "color":"#002552"}},
        row=1, col=1)
    fig.add_trace({
            "type":"scatter", "mode":"lines",
            "legendgroup":"top1",
            "showlegend":False,
            "x":evolution_df.index+1, "y":evolution_df["top1_time"],
            "line":{"color":"#002552"}},
        row=2, col=1)
    fig.update_layout({
        "title":"Evolução do treino",
        "height":700,
        "hovermode":"x unified",
        "legend_orientation":"h",
        "xaxis2":{"title":"Geração"}})
    return fig


zip_file = st.file_uploader("ZIP", type="zip")

if zip_file is not None:

    with zipfile.ZipFile(zip_file) as z:
        with z.open("experiments.json") as f:
            experiments_dict = json.load(f)
        with z.open("races.json") as f:
            races_dict = json.load(f)
        with z.open("cars.json") as f:
            cars_dict = json.load(f)
        with z.open("summary.json") as f:
            team_summary_dict = json.load(f)

    team:str = st.selectbox(
        "Equipe", team_summary_dict.keys())
    turn:str = st.selectbox(
        "Rodada", team_summary_dict[team].keys())
    
    st.write(f"## Resumo do {turn} de {team}")
    turn_dict:dict = team_summary_dict[team][turn]

    if turn_dict["evolution_exp"]:
        st.write("### Treinamento")
        
        exp_id:str = turn_dict["evolution_exp"]
        exp_dict:dict = experiments_dict[exp_id]

        track:str = exp_dict["race_track_path"]
        track = track.split("/")[-1].split(".")[0]
        st.write(f"Pista: {track}")

        if turn_dict["evolution_video"]:
            st.video(turn_dict["evolution_video"])
        
        standings_df:pd.DataFrame = get_standings_df(
            exp_dict["exhibition_race"], True)
        st.write("Resultado final")
        st.dataframe(standings_df)

        fig:go.Figure = get_evolution_plot(exp_id)
        st.plotly_chart(fig)
    
    if len(turn_dict["simulation_exp"]) > 0:
        st.write("### Simulação")

        if turn_dict["simulation_video"]:
            st.video(turn_dict["simulation_video"])

        for exp_id in turn_dict["simulation_exp"]:
            exp_dict:dict = experiments_dict[exp_id]
            track:str = exp_dict["race_track_path"]
            track = track.split("/")[-1].split(".")[0]
            st.write(f"Pista: {track}")
            standings_df:pd.DataFrame = get_standings_df(
            exp_dict["exhibition_race"], True)
            st.write("Resultado final")
            st.dataframe(standings_df)

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as subplots
import streamlit as st


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
    _df["elapsed_time"] = _df["elapsed_time"].where(_df["finished"], None)
    _df = _df.rename(columns={"car_id":"Corredor", "elapsed_time":"Tempo", "max_progress":"Distância"})
    _df = _df.sort_values(["finished", "Tempo", "Distância"], ascending=[False, True, False])
    _df = _df.drop(columns=["finished"])
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


with st.expander("Arquivos"):
    experiments_file = st.file_uploader("Experiments JSON", type="json")
    races_file = st.file_uploader("Races JSON", type="json")
    cars_file = st.file_uploader("Cars JSON", type="json")

experiments_dict:dict
races_dict:dict
cars_dict:dict

if experiments_file is not None:
    experiments_dict = json.load(experiments_file)
if races_file is not None:
    races_dict = json.load(races_file)
if cars_file is not None:
    cars_dict = json.load(cars_file)

team_summary_dict:dict = {
    "População inicial":{
        "Treino 0":{
            "evolution_exp":"0x00000",
            "evolution_video":"https://youtu.be/XcK_wWTky7Y",
            "simulation_exp":[],
            "simulation_video":"",},},
    "Bem Aleatório":{
        "Treino 1":{
            "evolution_exp":"0x00006",
            "evolution_video":"https://youtu.be/TUP7-_piQ-w",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
    "BFS":{
        "Treino 1":{
            "evolution_exp":"0x00005",
            "evolution_video":"https://youtu.be/h4Jt8J1bpzs",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
    "Machos Alfanuméricos":{
        "Treino 1":{
            "evolution_exp":"0x00001",
            "evolution_video":"https://youtu.be/ptbGXLUzOMg",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
    "Marcha-atrás":{
        "Treino 1":{
            "evolution_exp":"0x00007",
            "evolution_video":"https://youtu.be/xT-9g-NQevM",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
    "Meta-morfada":{
        "Treino 1":{
            "evolution_exp":"0x00004",
            "evolution_video":"https://youtu.be/hQToGi5qV8A",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
    "Quimera":{
        "Treino 1":{
            "evolution_exp":"0x00003",
            "evolution_video":"https://youtu.be/jkQdf2Qg4Vo",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
    "Viúvas do Funhaus":{
        "Treino 1":{
            "evolution_exp":"0x00002",
            "evolution_video":"https://youtu.be/zPKnj4imBEk",
            "simulation_exp":["0x00008", "0x00009"],
            "simulation_video":"https://youtu.be/_pKLgo6hEVM",},},
}

if experiments_dict and races_dict and cars_dict:

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

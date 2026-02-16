import pandas as pd

def ai_adjustments(df_ev, injuries_df=None, media_df=None):
    """
    Apply AI reasoning to adjust EV for each prop based on injuries, fatigue, and media info.
    Returns DataFrame with adjusted_EV, confidence, and AI_Context_Report.
    """
    df = df_ev.copy()
    adjusted_ev = []
    confidence = []
    context_report = []

    for idx, row in df.iterrows():
        player = row.get("PLAYER_NAME", "Unknown")
        ev = row.get("EV_Over", 0)
        # Placeholder: adjust EV based on injuries/media
        injury_status = ""
        media_info = ""
        if injuries_df is not None and not injuries_df.empty:
            injury_row = injuries_df[injuries_df["player"] == player]
            if not injury_row.empty:
                injury_status = injury_row.iloc[0]["status"]
        if media_df and player in media_df:
            media_info = media_df[player]

        # Simple logic: downgrade EV if injured/questionable
        adj_ev = ev
        conf = 7  # default confidence
        explanation = ""
        if injury_status:
            adj_ev -= 0.1
            conf -= 2
            explanation += f"Injury status: {injury_status}. "
        if media_info:
            explanation += f"Media info: {media_info}. "
            if "rest" in media_info.lower() or "fatigue" in media_info.lower():
                adj_ev -= 0.05
                conf -= 1
        if not explanation:
            explanation = "No relevant injury or media info."
        adjusted_ev.append(adj_ev)
        confidence.append(max(1, min(10, conf)))
        context_report.append(explanation)

    df["adjusted_EV"] = adjusted_ev
    df["confidence"] = confidence
    df["AI_Context_Report"] = context_report
    return df

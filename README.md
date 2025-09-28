# ⚽ Football Analytics Streamlit App

This Streamlit app scrapes match data from [WhoScored](https://whoscored.com) 
and generates interactive football visualizations:

- Shotmaps (Team)
- Pass Networks (Team)
- Box Passes (Team)
- Touchmap (Player) [hexbin style]
- Heatmap (Player) [KDE with cmasher colormap]
- Defensive Actions (Player)

## 🚀 Run Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py

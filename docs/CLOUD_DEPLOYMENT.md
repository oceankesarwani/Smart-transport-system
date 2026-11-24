# Streamlit Community Cloud deployment

Prepared on 24 November 2026. Public deployment has not succeeded: the available browser reached Streamlit's sign-in page rather than an authenticated cloud workspace. The repository is public, but the browser's GitHub login is not itself a Streamlit Cloud session. No public app URL is claimed.

## Minimum account steps

1. Open https://share.streamlit.io/ and sign in with the GitHub account that can deploy this repository. Complete any personal account setup or requested account authorization yourself.
2. Create app, choose existing app, and paste https://github.com/oceankesarwani/Smart-transport-system/blob/main/src/ui/app.py . Alternatively select repository `oceankesarwani/Smart-transport-system`, branch `main`, main file `src/ui/app.py`.
3. Open Advanced settings and select Python **3.11**. Leave secrets empty. Save and deploy. The `.python-version` file documents the local version; the cloud Python version must still be selected in Advanced settings.
4. Wait for the app to open, then verify S04 to S14, Thursday 18:00, Storm, event off, preference 2: +20.44% exposure reduction, 22 versus 25 minutes. Copy the actual assigned streamlit.app URL only after this succeeds.

## Readiness evidence

Root requirements.txt pins Scikit-learn 1.5.2, NumPy 1.26.4 and PyArrow 23.0.1; the model loader validates the artifact schema and Scikit-learn version. The trusted model is checked in at models/crowd_predictor.pkl. All source paths resolve from __file__ and lowercase src imports; Linux/Windows CI verify application tests. CI now explicitly loads the shipped model before retraining so platform incompatibility cannot be masked by CI regeneration. No paid services, API keys, sensors, credentials or secrets are needed by the application. No external font/map/CDN is needed by the native chart.

If cloud startup reports an incompatible model, reproduce `python -m src.model.train` with the pinned dependencies and commit the artifact; do not enter an API key or substitute invented predictions. Root .streamlit/config.toml supplies the tested theme. Cloud filesystem persistence is not required for normal prediction or routing.

Official configuration reference: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy (consulted 24 November 2026).

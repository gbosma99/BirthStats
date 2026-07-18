import streamlit as st
import pandas as pd
import plotly.express as px

# STEP 2 — Page Config
st.set_page_config(layout="wide")
st.title("Provisional Natality Data Dashboard")
st.markdown("### Birth Analysis by State and Gender")

DATA_FILE = "Provisional_Natality_2025_CDC.csv"

REQUIRED_FIELDS = [
    "state_of_residence",
    "month",
    "month_code",
    "year_code",
    "sex_of_infant",
    "births",
]

# STEP 3 — Load Data
df = None
load_error = False

try:
    raw_df = pd.read_csv(DATA_FILE)

    # Normalize column names
    raw_df.columns = (
        raw_df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    # Validate required logical fields
    missing_fields = [f for f in REQUIRED_FIELDS if f not in raw_df.columns]

    if missing_fields:
        st.error(
            "The dataset is missing required logical fields: "
            + ", ".join(missing_fields)
        )
        st.write("Actual columns found in dataset:")
        st.write(raw_df.columns)
        load_error = True
    else:
        df = raw_df.copy()
        # Convert births to numeric, drop nulls
        df["births"] = pd.to_numeric(df["births"], errors="coerce")
        df = df.dropna(subset=["births"])

except FileNotFoundError:
    st.error("Dataset file not found in repository.")
    load_error = True
except Exception as e:
    st.error(f"An unexpected error occurred while loading the dataset: {e}")
    load_error = True

if not load_error and df is not None and not df.empty:

    # STEP 4 — Sidebar Filters
    st.sidebar.header("Filters")

    month_options = ["All"] + sorted(df["month"].dropna().unique().tolist())
    sex_options = ["All"] + sorted(df["sex_of_infant"].dropna().unique().tolist())
    state_options = ["All"] + sorted(df["state_of_residence"].dropna().unique().tolist())

    selected_months = st.sidebar.multiselect(
        "Select Month(s)", options=month_options, default=["All"]
    )
    selected_sexes = st.sidebar.multiselect(
        "Select Gender(s)", options=sex_options, default=["All"]
    )
    selected_states = st.sidebar.multiselect(
        "Select State(s)", options=state_options, default=["All"]
    )

    # STEP 5 — Filtering Logic (does not modify original dataframe)
    filtered_df = df.copy()

    if "All" not in selected_months and len(selected_months) > 0:
        filtered_df = filtered_df[filtered_df["month"].isin(selected_months)]

    if "All" not in selected_sexes and len(selected_sexes) > 0:
        filtered_df = filtered_df[filtered_df["sex_of_infant"].isin(selected_sexes)]

    if "All" not in selected_states and len(selected_states) > 0:
        filtered_df = filtered_df[filtered_df["state_of_residence"].isin(selected_states)]

    # STEP 9 — Edge Case: Empty filter result
    if filtered_df.empty:
        st.warning("No data available for the selected filter combination.")
    else:
        # STEP 6 — Aggregation
        agg_df = (
            filtered_df.groupby(["state_of_residence", "sex_of_infant"], as_index=False)["births"]
            .sum()
            .sort_values("state_of_residence")
        )

        # STEP 7 — Plot
        fig = px.bar(
            agg_df,
            x="state_of_residence",
            y="births",
            color="sex_of_infant",
            title="Total Births by State and Gender",
            template="plotly_white",
        )
        fig.update_layout(
            legend_title_text="Gender",
            xaxis_title="State of Residence",
            yaxis_title="Total Births",
            autosize=True,
        )

        st.plotly_chart(fig, use_container_width=True)

        # STEP 8 — Show Filtered Table
        st.subheader("Filtered Data")
        st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

elif not load_error and df is not None and df.empty:
    st.warning("The dataset is empty after processing.")

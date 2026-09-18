import pandas as pd

df = pd.read_excel("Final Institute Lists/ICAR Agricultural & Allied Institutions.xlsx", sheet_name="Institutions Roster")
print("Roster shape:", df.shape)
print("Columns:", list(df.columns))
print()
print("Sample (first 5):")
for i, row in df.head(5).iterrows():
    print("  {}. [{}] {} | {} | {}".format(
        row["ICAR_Serial"], row["State"], row["Institution_Name"],
        row["University_Name"], row["Institution_Category"]
    ))
print()

no_state = df[df["State"] == "Not Specified"]
print("No-state records:", len(no_state))
for _, r in no_state.iterrows():
    print("  {} | {}".format(r["Institution_Name"], r["University_Name"]))

print()
print("State distribution:")
print(df["State"].value_counts().to_string())

print()
print("Category distribution:")
print(df["Institution_Category"].value_counts().to_string())

print()
print("Meghalaya records (checking if correct - was unexpectedly high):")
meg = df[df["State"] == "Meghalaya"]
for _, r in meg.iterrows():
    print("  {} | {}".format(r["Institution_Name"], r["University_Name"]))
